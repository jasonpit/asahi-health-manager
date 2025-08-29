import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

class AIIntegration:
    def __init__(self):
        self.claude_api_key = None
        self.openai_api_key = None
        self.session = None
        self.claude_base_url = "https://api.anthropic.com/v1"
        self.openai_base_url = "https://api.openai.com/v1"
        
    async def initialize(self):
        """Initialize AI integration with API keys"""
        self.claude_api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.claude_api_key and not self.openai_api_key:
            logging.warning("No AI API keys found. AI features will be disabled.")
            return False
            
        self.session = aiohttp.ClientSession()
        
        # Test API connections
        claude_available = await self._test_claude_connection()
        openai_available = await self._test_openai_connection()
        
        logging.info(f"AI Integration initialized - Claude: {'✓' if claude_available else '✗'}, OpenAI: {'✓' if openai_available else '✗'}")
        return claude_available or openai_available
    
    async def _test_claude_connection(self) -> bool:
        """Test Claude API connection"""
        if not self.claude_api_key:
            return False
            
        try:
            headers = {
                'x-api-key': self.claude_api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            test_payload = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 10,
                'messages': [
                    {'role': 'user', 'content': 'Test connection'}
                ]
            }
            
            async with self.session.post(
                f"{self.claude_base_url}/messages",
                headers=headers,
                json=test_payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logging.error(f"Claude API test failed: {e}")
            return False
    
    async def _test_openai_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.openai_api_key:
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            test_payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'user', 'content': 'Test'}
                ],
                'max_tokens': 5
            }
            
            async with self.session.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logging.error(f"OpenAI API test failed: {e}")
            return False
    
    async def analyze_system_health(self, scan_results: Dict[str, Any], use_claude: bool = True) -> Dict[str, Any]:
        """Analyze system health using AI"""
        
        prompt = self._build_system_analysis_prompt(scan_results)
        
        if use_claude and self.claude_api_key:
            response = await self._query_claude(prompt, model='claude-3-sonnet-20240229')
        elif self.openai_api_key:
            response = await self._query_openai(prompt, model='gpt-4-turbo-preview')
        else:
            return {'error': 'No AI service available'}
        
        return await self._parse_analysis_response(response)
    
    async def get_fix_recommendations(self, issues: List[Dict[str, Any]], use_claude: bool = True) -> List[Dict[str, Any]]:
        """Get AI-powered fix recommendations"""
        
        prompt = self._build_fix_recommendations_prompt(issues)
        
        if use_claude and self.claude_api_key:
            response = await self._query_claude(prompt, model='claude-3-sonnet-20240229')
        elif self.openai_api_key:
            response = await self._query_openai(prompt, model='gpt-4-turbo-preview')
        else:
            return [{'error': 'No AI service available'}]
        
        return await self._parse_recommendations_response(response)
    
    async def search_latest_solutions(self, issue_description: str, use_claude: bool = True) -> Dict[str, Any]:
        """Search for latest solutions to specific issues"""
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""
        Current date: {current_date}
        
        Search for the most recent solutions, patches, or workarounds for this Asahi Linux issue:
        
        Issue: {issue_description}
        
        Please provide:
        1. Recent developments or patches (2024-2025)
        2. Community solutions from Reddit, GitHub, or Asahi forums
        3. Upstream kernel status if applicable
        4. Step-by-step fix instructions
        5. Prevention measures
        
        Focus on solutions that are current and tested on recent Asahi Linux versions.
        """
        
        if use_claude and self.claude_api_key:
            response = await self._query_claude(prompt, model='claude-3-sonnet-20240229')
        elif self.openai_api_key:
            response = await self._query_openai(prompt, model='gpt-4-turbo-preview')
        else:
            return {'error': 'No AI service available'}
        
        return await self._parse_solution_response(response)
    
    def _build_system_analysis_prompt(self, scan_results: Dict[str, Any]) -> str:
        """Build prompt for system analysis"""
        
        # Summarize key findings for the prompt
        key_issues = []
        
        if 'os_health' in scan_results:
            os_health = scan_results['os_health']
            
            # Memory issues
            if os_health.get('memory_usage', {}).get('memory_pressure', False):
                key_issues.append(f"High memory usage: {os_health['memory_usage'].get('memory_percent', 0):.1f}%")
            
            # Disk issues  
            disk_usage = os_health.get('disk_usage', {}).get('partitions', {})
            for mount, info in disk_usage.items():
                if info.get('critical', False):
                    key_issues.append(f"Critical disk usage on {mount}: {info.get('percent', 0):.1f}%")
            
            # Kernel issues
            kernel_messages = os_health.get('kernel_health', {}).get('kernel_messages', [])
            if kernel_messages:
                key_issues.append(f"Kernel errors detected: {len(kernel_messages)} recent errors")
            
            # Asahi-specific issues
            asahi_issues = os_health.get('asahi_specific', {})
            for category, issues in asahi_issues.items():
                if isinstance(issues, list) and issues:
                    key_issues.extend(issues)
            
            # Failed services
            failed_services = os_health.get('systemd_services', {}).get('failed_services', [])
            if failed_services:
                key_issues.append(f"Failed systemd services: {', '.join(failed_services[:3])}")
        
        prompt = f"""
        You are an expert system administrator specializing in Asahi Linux on Apple Silicon Macs.
        
        Analyze the following system scan results and provide:
        
        1. **Critical Issues**: Problems requiring immediate attention
        2. **Performance Issues**: Things affecting system performance  
        3. **Stability Issues**: Problems that could cause crashes or instability
        4. **Asahi-Specific Issues**: Problems unique to Asahi Linux/Apple Silicon
        5. **Preventive Measures**: Actions to prevent future problems
        
        Key Issues Detected:
        {chr(10).join([f"- {issue}" for issue in key_issues]) if key_issues else "- No critical issues detected"}
        
        Full System Scan Results:
        {json.dumps(scan_results, indent=2, default=str)[:8000]}  # Limit size
        
        Provide specific, actionable recommendations with:
        - Severity level (Critical/High/Medium/Low)
        - Impact description
        - Specific fix commands or steps
        - Risk assessment for each fix
        
        Format your response as structured JSON.
        """
        
        return prompt
    
    def _build_fix_recommendations_prompt(self, issues: List[Dict[str, Any]]) -> str:
        """Build prompt for fix recommendations"""
        
        issues_text = "\n".join([
            f"- {issue.get('description', str(issue))}" for issue in issues
        ])
        
        prompt = f"""
        You are an expert Asahi Linux system administrator. Provide specific fix recommendations for these issues:
        
        Issues to Fix:
        {issues_text}
        
        For each issue, provide:
        1. **Root Cause Analysis**: Why this issue occurred
        2. **Fix Steps**: Detailed commands or procedures  
        3. **Risk Assessment**: Potential risks of the fix
        4. **Verification**: How to confirm the fix worked
        5. **Prevention**: How to prevent recurrence
        
        Consider Asahi Linux specifics:
        - 16K page size compatibility issues
        - Apple Silicon hardware limitations
        - Downstream kernel patches
        - macOS dual-boot requirements
        
        Prioritize fixes by:
        - System stability impact
        - Data safety
        - Ease of implementation
        
        Format as JSON with structured recommendations.
        """
        
        return prompt
    
    async def _query_claude(self, prompt: str, model: str = 'claude-3-sonnet-20240229') -> str:
        """Query Claude API"""
        if not self.claude_api_key:
            return "Claude API key not available"
        
        try:
            headers = {
                'x-api-key': self.claude_api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            payload = {
                'model': model,
                'max_tokens': 4000,
                'messages': [
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ]
            }
            
            async with self.session.post(
                f"{self.claude_base_url}/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result['content'][0]['text']
                else:
                    error_text = await response.text()
                    logging.error(f"Claude API error {response.status}: {error_text}")
                    return f"Claude API error: {response.status}"
                    
        except Exception as e:
            logging.error(f"Claude query failed: {e}")
            return f"Claude query failed: {str(e)}"
    
    async def _query_openai(self, prompt: str, model: str = 'gpt-4-turbo-preview') -> str:
        """Query OpenAI API"""
        if not self.openai_api_key:
            return "OpenAI API key not available"
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert Asahi Linux system administrator with deep knowledge of Apple Silicon Macs and Linux system administration.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 4000,
                'temperature': 0.1
            }
            
            async with self.session.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    logging.error(f"OpenAI API error {response.status}: {error_text}")
                    return f"OpenAI API error: {response.status}"
                    
        except Exception as e:
            logging.error(f"OpenAI query failed: {e}")
            return f"OpenAI query failed: {str(e)}"
    
    async def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: structure the text response
                return {
                    'raw_analysis': response,
                    'structured': False,
                    'timestamp': datetime.now().isoformat()
                }
        except json.JSONDecodeError:
            return {
                'raw_analysis': response,
                'structured': False,
                'parse_error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _parse_recommendations_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI recommendations response"""
        try:
            # Try to extract JSON
            if '[' in response and ']' in response:
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            elif '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                return [parsed] if isinstance(parsed, dict) else parsed
            else:
                # Parse text response into structured format
                return [{
                    'raw_recommendation': response,
                    'structured': False,
                    'timestamp': datetime.now().isoformat()
                }]
        except json.JSONDecodeError:
            return [{
                'raw_recommendation': response,
                'structured': False,
                'parse_error': True,
                'timestamp': datetime.now().isoformat()
            }]
    
    async def _parse_solution_response(self, response: str) -> Dict[str, Any]:
        """Parse AI solution search response"""
        try:
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {
                    'solution_text': response,
                    'structured': False,
                    'timestamp': datetime.now().isoformat()
                }
        except json.JSONDecodeError:
            return {
                'solution_text': response,
                'structured': False,
                'parse_error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()