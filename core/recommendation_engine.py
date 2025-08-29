import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Category(Enum):
    SYSTEM = "system"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ASAHI_SPECIFIC = "asahi_specific"

@dataclass
class Recommendation:
    id: str
    title: str
    description: str
    severity: Severity
    category: Category
    impact: str
    fix_commands: List[str]
    fix_description: str
    risk_level: str
    verification_commands: List[str]
    prevention_measures: List[str]
    estimated_time: str
    requires_reboot: bool
    backup_recommended: bool
    ai_confidence: float
    created_at: str
    
class RecommendationEngine:
    def __init__(self):
        self.ai_integration = None
        self.recommendations_cache = {}
        self.rules_engine = AsahiRulesEngine()
        
    async def initialize(self):
        """Initialize recommendation engine"""
        from .ai_integration import AIIntegration
        self.ai_integration = AIIntegration()
        await self.ai_integration.initialize()
        
    async def generate_recommendations(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive recommendations from scan results"""
        
        all_recommendations = []
        
        # Rule-based recommendations (fast, reliable)
        rule_based_recs = await self.rules_engine.generate_recommendations(scan_results)
        all_recommendations.extend(rule_based_recs)
        
        # AI-powered recommendations (comprehensive, contextual)
        if self.ai_integration:
            ai_recs = await self._generate_ai_recommendations(scan_results)
            all_recommendations.extend(ai_recs)
        
        # Merge and prioritize recommendations
        merged_recs = await self._merge_and_prioritize(all_recommendations)
        
        # Add metadata and validation
        final_recs = await self._finalize_recommendations(merged_recs, scan_results)
        
        return final_recs
    
    async def _generate_ai_recommendations(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations"""
        try:
            # Get AI analysis
            analysis = await self.ai_integration.analyze_system_health(scan_results)
            
            if 'error' in analysis:
                logging.warning(f"AI analysis failed: {analysis['error']}")
                return []
            
            # Extract issues from analysis
            issues = self._extract_issues_from_analysis(analysis)
            
            if not issues:
                return []
            
            # Get detailed fix recommendations
            ai_recommendations = await self.ai_integration.get_fix_recommendations(issues)
            
            # Convert AI recommendations to our format
            formatted_recs = []
            for i, rec in enumerate(ai_recommendations):
                if 'error' in rec:
                    continue
                    
                formatted_rec = self._format_ai_recommendation(rec, i)
                if formatted_rec:
                    formatted_recs.append(formatted_rec)
            
            return formatted_recs
            
        except Exception as e:
            logging.error(f"AI recommendation generation failed: {e}")
            return []
    
    def _extract_issues_from_analysis(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable issues from AI analysis"""
        issues = []
        
        if 'structured' in analysis and not analysis['structured']:
            # Parse unstructured analysis
            text = analysis.get('raw_analysis', '')
            # Simple heuristic parsing - in production, this would be more sophisticated
            lines = text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['error', 'critical', 'fail', 'issue', 'problem']):
                    issues.append({'description': line.strip()})
        else:
            # Extract from structured analysis
            for category in ['critical_issues', 'performance_issues', 'stability_issues', 'asahi_specific_issues']:
                if category in analysis:
                    category_issues = analysis[category]
                    if isinstance(category_issues, list):
                        for issue in category_issues:
                            if isinstance(issue, dict):
                                issues.append(issue)
                            else:
                                issues.append({'description': str(issue)})
        
        return issues
    
    def _format_ai_recommendation(self, ai_rec: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Format AI recommendation to our standard format"""
        try:
            rec_id = f"ai_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract fields with fallbacks
            title = ai_rec.get('title', ai_rec.get('issue', f'AI Recommendation {index + 1}'))
            description = ai_rec.get('description', ai_rec.get('root_cause', ''))
            
            # Parse severity
            severity_str = ai_rec.get('severity', 'medium').lower()
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.MEDIUM
            
            # Parse category
            category_str = ai_rec.get('category', 'system').lower()
            try:
                category = Category(category_str)
            except ValueError:
                category = Category.SYSTEM
            
            # Extract fix information
            fix_steps = ai_rec.get('fix_steps', ai_rec.get('solution', []))
            if isinstance(fix_steps, str):
                fix_steps = [fix_steps]
            
            fix_commands = []
            fix_description = ""
            
            for step in fix_steps:
                if isinstance(step, dict):
                    if 'command' in step:
                        fix_commands.append(step['command'])
                    if 'description' in step:
                        fix_description += step['description'] + "\n"
                else:
                    # Try to detect if it's a command or description
                    if any(cmd in str(step) for cmd in ['sudo', 'systemctl', 'pacman', 'dnf', 'apt']):
                        fix_commands.append(str(step))
                    else:
                        fix_description += str(step) + "\n"
            
            # Extract verification steps
            verification = ai_rec.get('verification', ai_rec.get('verify', []))
            if isinstance(verification, str):
                verification = [verification]
            
            verification_commands = []
            for ver in verification:
                if isinstance(ver, dict) and 'command' in ver:
                    verification_commands.append(ver['command'])
                elif isinstance(ver, str):
                    verification_commands.append(ver)
            
            # Extract prevention measures
            prevention = ai_rec.get('prevention', ai_rec.get('prevent_recurrence', []))
            if isinstance(prevention, str):
                prevention = [prevention]
            
            recommendation = Recommendation(
                id=rec_id,
                title=title,
                description=description,
                severity=severity,
                category=category,
                impact=ai_rec.get('impact', 'System functionality may be affected'),
                fix_commands=fix_commands,
                fix_description=fix_description.strip(),
                risk_level=ai_rec.get('risk_assessment', ai_rec.get('risk', 'medium')),
                verification_commands=verification_commands,
                prevention_measures=prevention if isinstance(prevention, list) else [str(prevention)],
                estimated_time=ai_rec.get('estimated_time', '5-10 minutes'),
                requires_reboot=ai_rec.get('requires_reboot', False),
                backup_recommended=ai_rec.get('backup_recommended', severity in [Severity.CRITICAL, Severity.HIGH]),
                ai_confidence=ai_rec.get('confidence', 0.7),
                created_at=datetime.now().isoformat()
            )
            
            return asdict(recommendation)
            
        except Exception as e:
            logging.error(f"Failed to format AI recommendation: {e}")
            return None
    
    async def _merge_and_prioritize(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar recommendations and prioritize by severity/impact"""
        
        # Group similar recommendations
        grouped = {}
        for rec in recommendations:
            # Simple similarity grouping by title similarity
            title = rec.get('title', '').lower()
            found_group = False
            
            for group_key in grouped.keys():
                if self._calculate_similarity(title, group_key) > 0.7:
                    grouped[group_key].append(rec)
                    found_group = True
                    break
            
            if not found_group:
                grouped[title] = [rec]
        
        # Merge grouped recommendations
        merged = []
        for group in grouped.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged_rec = await self._merge_recommendations(group)
                merged.append(merged_rec)
        
        # Sort by priority
        severity_order = {
            'critical': 0,
            'high': 1, 
            'medium': 2,
            'low': 3,
            'info': 4
        }
        
        merged.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'medium'), 2),
            -x.get('ai_confidence', 0.5)
        ))
        
        return merged
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def _merge_recommendations(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge similar recommendations"""
        # Take the highest severity recommendation as base
        base_rec = max(group, key=lambda x: {
            'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0
        }.get(x.get('severity', 'medium'), 2))
        
        # Merge fix commands and descriptions
        all_commands = []
        all_descriptions = []
        all_verifications = []
        all_preventions = []
        
        for rec in group:
            commands = rec.get('fix_commands', [])
            if isinstance(commands, list):
                all_commands.extend(commands)
            
            desc = rec.get('fix_description', '')
            if desc:
                all_descriptions.append(desc)
            
            verifs = rec.get('verification_commands', [])
            if isinstance(verifs, list):
                all_verifications.extend(verifs)
            
            preventions = rec.get('prevention_measures', [])
            if isinstance(preventions, list):
                all_preventions.extend(preventions)
        
        # Remove duplicates while preserving order
        base_rec['fix_commands'] = list(dict.fromkeys(all_commands))
        base_rec['fix_description'] = "\n\n".join(all_descriptions)
        base_rec['verification_commands'] = list(dict.fromkeys(all_verifications))
        base_rec['prevention_measures'] = list(dict.fromkeys(all_preventions))
        
        # Update confidence as average
        confidences = [rec.get('ai_confidence', 0.5) for rec in group]
        base_rec['ai_confidence'] = sum(confidences) / len(confidences)
        
        return base_rec
    
    async def _finalize_recommendations(self, recommendations: List[Dict[str, Any]], scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add final metadata and validate recommendations"""
        
        finalized = []
        
        for rec in recommendations:
            # Add system context
            rec['system_context'] = {
                'hostname': scan_results.get('os_health', {}).get('system_info', {}).get('hostname', 'unknown'),
                'kernel': scan_results.get('os_health', {}).get('system_info', {}).get('kernel', 'unknown'),
                'distribution': scan_results.get('os_health', {}).get('system_info', {}).get('distribution', 'unknown')
            }
            
            # Validate commands
            rec['fix_commands'] = await self._validate_commands(rec.get('fix_commands', []))
            
            # Add safety warnings
            rec['safety_warnings'] = await self._generate_safety_warnings(rec)
            
            # Estimate impact
            rec['estimated_impact'] = await self._estimate_impact(rec, scan_results)
            
            finalized.append(rec)
        
        return finalized
    
    async def _validate_commands(self, commands: List[str]) -> List[str]:
        """Validate and sanitize fix commands"""
        validated = []
        dangerous_patterns = ['rm -rf', 'dd if=', 'mkfs', 'fdisk', '>>', 'curl | sh', 'wget | sh']
        
        for cmd in commands:
            if isinstance(cmd, str) and cmd.strip():
                # Check for dangerous patterns
                if any(pattern in cmd.lower() for pattern in dangerous_patterns):
                    cmd = f"# WARNING: Potentially dangerous command - review carefully\n{cmd}"
                
                # Ensure proper quoting for paths with spaces
                if '/Users/' in cmd or '/home/' in cmd:
                    # This is a simplified check - production would be more sophisticated
                    pass
                
                validated.append(cmd.strip())
        
        return validated
    
    async def _generate_safety_warnings(self, recommendation: Dict[str, Any]) -> List[str]:
        """Generate safety warnings for recommendations"""
        warnings = []
        
        severity = recommendation.get('severity', 'medium')
        if severity in ['critical', 'high']:
            warnings.append("High-impact change - create system backup before proceeding")
        
        if recommendation.get('requires_reboot', False):
            warnings.append("System reboot required - save all work before applying")
        
        fix_commands = recommendation.get('fix_commands', [])
        for cmd in fix_commands:
            if 'sudo' in cmd:
                warnings.append("Requires administrative privileges")
                break
        
        if recommendation.get('risk_level', 'medium').lower() in ['high', 'critical']:
            warnings.append("High-risk operation - review commands carefully")
        
        return list(set(warnings))  # Remove duplicates
    
    async def _estimate_impact(self, recommendation: Dict[str, Any], scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the impact of applying a recommendation"""
        
        impact = {
            'performance_improvement': 'unknown',
            'stability_improvement': 'unknown',
            'affected_services': [],
            'downtime_estimate': '0 minutes'
        }
        
        # Analyze based on category and commands
        category = recommendation.get('category', 'system')
        commands = recommendation.get('fix_commands', [])
        
        if category == 'performance':
            impact['performance_improvement'] = 'medium to high'
        
        if any('systemctl' in cmd for cmd in commands):
            # Extract service names
            for cmd in commands:
                if 'systemctl' in cmd:
                    parts = cmd.split()
                    if len(parts) > 2:
                        service = parts[-1]
                        impact['affected_services'].append(service)
        
        if recommendation.get('requires_reboot', False):
            impact['downtime_estimate'] = '2-5 minutes (reboot)'
        elif impact['affected_services']:
            impact['downtime_estimate'] = '30 seconds - 2 minutes'
        
        return impact
    
    async def generate_detailed_report(self, scan_results: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_version': '1.0',
                'system_info': scan_results.get('os_health', {}).get('system_info', {}),
                'scan_duration': 'unknown'  # Would be calculated in practice
            },
            'executive_summary': await self._generate_executive_summary(scan_results, recommendations),
            'system_health_overview': await self._generate_health_overview(scan_results),
            'detailed_findings': await self._organize_findings_by_category(scan_results),
            'recommendations': {
                'total_count': len(recommendations),
                'by_severity': self._count_by_severity(recommendations),
                'detailed_recommendations': recommendations
            },
            'trend_analysis': await self._generate_trend_analysis(scan_results),
            'next_steps': await self._generate_next_steps(recommendations),
            'appendices': {
                'raw_scan_data': scan_results,
                'glossary': self._get_glossary(),
                'references': self._get_references()
            }
        }
        
        return report
    
    async def _generate_executive_summary(self, scan_results: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary"""
        
        critical_count = len([r for r in recommendations if r.get('severity') == 'critical'])
        high_count = len([r for r in recommendations if r.get('severity') == 'high'])
        
        summary = {
            'overall_health': 'good',
            'critical_issues_count': critical_count,
            'high_priority_issues_count': high_count,
            'key_findings': [],
            'immediate_actions_required': critical_count > 0 or high_count > 2
        }
        
        # Determine overall health
        if critical_count > 0:
            summary['overall_health'] = 'critical'
        elif high_count > 2:
            summary['overall_health'] = 'concerning'
        elif high_count > 0:
            summary['overall_health'] = 'fair'
        
        # Extract key findings
        os_health = scan_results.get('os_health', {})
        
        # Memory usage
        memory = os_health.get('memory_usage', {})
        if memory.get('memory_pressure', False):
            summary['key_findings'].append(f"High memory usage detected: {memory.get('memory_percent', 0):.1f}%")
        
        # Disk usage
        disk_critical = False
        disk_usage = os_health.get('disk_usage', {}).get('partitions', {})
        for mount, info in disk_usage.items():
            if info.get('critical', False):
                disk_critical = True
                summary['key_findings'].append(f"Critical disk space on {mount}: {info.get('percent', 0):.1f}% used")
        
        # Asahi-specific issues
        asahi_issues = os_health.get('asahi_specific', {})
        total_asahi_issues = sum(len(issues) if isinstance(issues, list) else 1 for issues in asahi_issues.values())
        if total_asahi_issues > 0:
            summary['key_findings'].append(f"{total_asahi_issues} Asahi Linux specific issues detected")
        
        return summary
    
    async def _generate_health_overview(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system health overview"""
        
        overview = {
            'system_uptime': 'unknown',
            'load_average': 'unknown',
            'memory_health': 'good',
            'disk_health': 'good',
            'network_health': 'good',
            'service_health': 'good'
        }
        
        os_health = scan_results.get('os_health', {})
        
        # System info
        system_info = os_health.get('system_info', {})
        overview['system_uptime'] = system_info.get('uptime', 'unknown')
        
        # Memory health
        memory = os_health.get('memory_usage', {})
        memory_percent = memory.get('memory_percent', 0)
        if memory_percent > 90:
            overview['memory_health'] = 'critical'
        elif memory_percent > 75:
            overview['memory_health'] = 'concerning'
        
        # Disk health
        disk_usage = os_health.get('disk_usage', {}).get('partitions', {})
        max_disk_usage = max((info.get('percent', 0) for info in disk_usage.values()), default=0)
        if max_disk_usage > 90:
            overview['disk_health'] = 'critical'
        elif max_disk_usage > 80:
            overview['disk_health'] = 'concerning'
        
        # Network health
        network = os_health.get('network_health', {})
        connectivity = network.get('connectivity', {})
        if not connectivity.get('internet', True):
            overview['network_health'] = 'poor'
        elif not connectivity.get('dns', True):
            overview['network_health'] = 'concerning'
        
        # Service health
        services = os_health.get('systemd_services', {})
        failed_count = services.get('failed', 0)
        if failed_count > 5:
            overview['service_health'] = 'poor'
        elif failed_count > 0:
            overview['service_health'] = 'concerning'
        
        return overview
    
    async def _organize_findings_by_category(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Organize findings by category"""
        
        findings = {
            'system_health': [],
            'hardware_status': [],
            'software_issues': [],
            'network_connectivity': [],
            'security_concerns': [],
            'asahi_specific': []
        }
        
        os_health = scan_results.get('os_health', {})
        
        # System health findings
        memory = os_health.get('memory_usage', {})
        if memory.get('memory_pressure', False):
            findings['system_health'].append({
                'issue': 'High memory usage',
                'details': f"Memory usage at {memory.get('memory_percent', 0):.1f}%",
                'severity': 'high' if memory.get('memory_percent', 0) > 95 else 'medium'
            })
        
        # Hardware findings
        thermal = os_health.get('thermal_status', {})
        thermal_zones = thermal.get('thermal_zones', {})
        for zone, info in thermal_zones.items():
            if info.get('critical', False):
                findings['hardware_status'].append({
                    'issue': f'High temperature in {zone}',
                    'details': f"Temperature: {info.get('temperature', 0):.1f}°C",
                    'severity': 'high'
                })
        
        # Asahi-specific findings
        asahi_issues = os_health.get('asahi_specific', {})
        for category, issues in asahi_issues.items():
            if isinstance(issues, list):
                for issue in issues:
                    findings['asahi_specific'].append({
                        'issue': category.replace('_', ' ').title(),
                        'details': str(issue),
                        'severity': 'medium'
                    })
        
        return findings
    
    def _count_by_severity(self, recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count recommendations by severity"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        for rec in recommendations:
            severity = rec.get('severity', 'medium')
            counts[severity] = counts.get(severity, 0) + 1
        
        return counts
    
    async def _generate_trend_analysis(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis (would compare with historical data)"""
        return {
            'note': 'Trend analysis requires historical data',
            'current_snapshot': datetime.now().isoformat(),
            'recommendations': [
                'Enable regular scanning to build trend analysis',
                'Monitor key metrics over time',
                'Set up alerts for degrading trends'
            ]
        }
    
    async def _generate_next_steps(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommended next steps"""
        critical_count = len([r for r in recommendations if r.get('severity') == 'critical'])
        high_count = len([r for r in recommendations if r.get('severity') == 'high'])
        
        next_steps = []
        
        if critical_count > 0:
            next_steps.append(f"Immediately address {critical_count} critical issue(s)")
            next_steps.append("Create system backup before making changes")
        
        if high_count > 0:
            next_steps.append(f"Plan to address {high_count} high-priority issue(s) within 24-48 hours")
        
        next_steps.extend([
            "Schedule regular system health scans",
            "Monitor system performance after applying fixes",
            "Update system packages regularly",
            "Review Asahi Linux community updates for new developments"
        ])
        
        return next_steps
    
    def _get_glossary(self) -> Dict[str, str]:
        """Get glossary of technical terms"""
        return {
            "16K Page Size": "Asahi Linux uses 16K memory pages instead of the standard 4K, which can cause compatibility issues with some software",
            "m1n1": "The bootloader used by Asahi Linux on Apple Silicon Macs",
            "DRM": "Direct Rendering Manager - kernel subsystem for GPU access",
            "APFS": "Apple File System used by macOS",
            "ProMotion": "Apple's variable refresh rate display technology"
        }
    
    def _get_references(self) -> List[str]:
        """Get reference links"""
        return [
            "Asahi Linux Documentation: https://asahilinux.org/docs/",
            "Asahi Linux GitHub: https://github.com/AsahiLinux",
            "Community Support: https://asahilinux.org/community/",
            "Known Issues: https://github.com/AsahiLinux/docs/wiki/Broken-Software"
        ]

class AsahiRulesEngine:
    """Rule-based recommendation engine for common Asahi Linux issues"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load predefined rules for common issues"""
        return [
            {
                'id': 'high_memory_usage',
                'condition': lambda results: results.get('os_health', {}).get('memory_usage', {}).get('memory_percent', 0) > 85,
                'recommendation': {
                    'title': 'High Memory Usage Detected',
                    'severity': 'high',
                    'category': 'performance',
                    'description': 'System memory usage is above 85%, which may cause performance issues',
                    'fix_commands': [
                        'sudo systemctl restart systemd-oomd',
                        'free -h',
                        'ps aux --sort=-%mem | head -10'
                    ],
                    'fix_description': 'Restart OOM daemon and identify memory-hungry processes'
                }
            },
            {
                'id': 'disk_space_critical',
                'condition': lambda results: any(
                    info.get('critical', False) 
                    for info in results.get('os_health', {}).get('disk_usage', {}).get('partitions', {}).values()
                ),
                'recommendation': {
                    'title': 'Critical Disk Space Issue',
                    'severity': 'critical',
                    'category': 'system',
                    'description': 'One or more partitions are critically low on disk space',
                    'fix_commands': [
                        'sudo pacman -Sc',
                        'sudo journalctl --vacuum-time=7d',
                        'du -sh /var/log/* | sort -hr',
                        'df -h'
                    ],
                    'fix_description': 'Clean package cache, rotate logs, and check disk usage'
                }
            },
            {
                'id': 'rust_jemalloc_issue',
                'condition': lambda results: any(
                    'rust' in issue.lower() and 'jemalloc' in issue.lower()
                    for issues in results.get('os_health', {}).get('asahi_specific', {}).values()
                    if isinstance(issues, list)
                    for issue in issues
                ),
                'recommendation': {
                    'title': 'Rust/jemalloc 16K Page Size Issue',
                    'severity': 'medium',
                    'category': 'asahi_specific',
                    'description': 'Rust from Arch repos may not work with 16K page size',
                    'fix_commands': [
                        'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh',
                        'source ~/.cargo/env',
                        'rustup default stable'
                    ],
                    'fix_description': 'Install Rust via rustup instead of system packages'
                }
            },
            {
                'id': 'failed_services',
                'condition': lambda results: len(results.get('os_health', {}).get('systemd_services', {}).get('failed_services', [])) > 0,
                'recommendation': {
                    'title': 'Failed Systemd Services',
                    'severity': 'medium',
                    'category': 'system',
                    'description': 'One or more systemd services have failed',
                    'fix_commands': [
                        'systemctl --failed',
                        'sudo systemctl reset-failed'
                    ],
                    'fix_description': 'Review failed services and reset their state'
                }
            }
        ]
    
    async def generate_recommendations(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rule-based recommendations"""
        recommendations = []
        
        for rule in self.rules:
            try:
                if rule['condition'](scan_results):
                    rec = rule['recommendation'].copy()
                    rec['id'] = f"rule_{rule['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    rec['ai_confidence'] = 1.0  # Rule-based = high confidence
                    rec['created_at'] = datetime.now().isoformat()
                    
                    # Add defaults
                    rec.setdefault('impact', 'System performance or stability may be affected')
                    rec.setdefault('risk_level', 'low')
                    rec.setdefault('verification_commands', [])
                    rec.setdefault('prevention_measures', [])
                    rec.setdefault('estimated_time', '5 minutes')
                    rec.setdefault('requires_reboot', False)
                    rec.setdefault('backup_recommended', False)
                    
                    recommendations.append(rec)
                    
            except Exception as e:
                logging.error(f"Rule {rule['id']} failed: {e}")
        
        return recommendations