import asyncio
import subprocess
import json
import os
import psutil
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

class SystemScanner:
    def __init__(self):
        self.scan_results = {}
        self.asahi_specific_checks = True
        
    async def initialize(self):
        """Initialize the scanner"""
        self.kernel_version = platform.release()
        self.is_asahi = '16k' in self.kernel_version.lower()
        
    async def scan_os_health(self) -> Dict[str, Any]:
        """Comprehensive OS health scan for Asahi Linux"""
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': await self._get_system_info(),
            'kernel_health': await self._check_kernel_health(),
            'memory_usage': await self._check_memory_usage(),
            'disk_usage': await self._check_disk_usage(),
            'boot_issues': await self._check_boot_issues(),
            'display_issues': await self._check_display_issues(),
            'power_management': await self._check_power_management(),
            'thermal_status': await self._check_thermal_status(),
            'network_health': await self._check_network_health(),
            'systemd_services': await self._check_systemd_services(),
            'asahi_specific': await self._check_asahi_specific_issues(),
        }
        return health_data
    
    async def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information"""
        try:
            uname = os.uname()
            return {
                'hostname': socket.gethostname(),
                'kernel': uname.release,
                'architecture': uname.machine,
                'distribution': await self._get_distribution(),
                'uptime': await self._get_uptime(),
                'cpu_info': await self._get_cpu_info(),
                'apple_chip': await self._detect_apple_chip(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _get_distribution(self) -> str:
        """Detect Linux distribution"""
        try:
            if Path('/etc/arch-release').exists():
                return 'Arch Linux'
            elif Path('/etc/fedora-release').exists():
                with open('/etc/fedora-release') as f:
                    return f.read().strip()
            else:
                result = await self._run_command(['lsb_release', '-d'])
                if result['returncode'] == 0:
                    return result['stdout'].split(':')[1].strip()
                return 'Unknown'
        except:
            return 'Unknown'
    
    async def _get_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{days}d {hours}h {minutes}m"
        except:
            return "Unknown"
    
    async def _get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information"""
        try:
            cpu_info = {}
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('model name'):
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
                    elif line.startswith('Hardware'):
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
            
            cpu_info['cores'] = str(psutil.cpu_count(logical=False))
            cpu_info['threads'] = str(psutil.cpu_count(logical=True))
            cpu_info['frequency'] = f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Unknown"
            return cpu_info
        except Exception as e:
            return {'error': str(e)}
    
    async def _detect_apple_chip(self) -> str:
        """Detect Apple Silicon chip type"""
        try:
            result = await self._run_command(['sysctl', '-n', 'hw.model'])
            if result['returncode'] == 0:
                model = result['stdout'].strip()
                if 'Mac' in model:
                    # Try to extract M1/M2/M3/M4 info
                    chip_match = re.search(r'(M\d+)', model)
                    if chip_match:
                        return f"Apple {chip_match.group(1)}"
                return model
            
            # Fallback: check device tree
            dt_path = Path('/proc/device-tree/compatible')
            if dt_path.exists():
                with open(dt_path, 'rb') as f:
                    compatible = f.read().decode('utf-8', errors='ignore')
                    if 'apple' in compatible.lower():
                        return f"Apple Silicon ({compatible.split(',')[0]})"
            
            return "Unknown Apple Silicon"
        except:
            return "Unknown"
    
    async def _check_kernel_health(self) -> Dict[str, Any]:
        """Check kernel health and Asahi-specific issues"""
        kernel_health = {
            'version': platform.release(),
            'is_asahi_kernel': '16k' in platform.release().lower(),
            'page_size': await self._get_page_size(),
            'kernel_messages': await self._check_kernel_messages(),
            'loaded_modules': await self._check_loaded_modules(),
            'kernel_params': await self._get_kernel_parameters(),
        }
        return kernel_health
    
    async def _get_page_size(self) -> str:
        """Get kernel page size"""
        try:
            result = await self._run_command(['getconf', 'PAGESIZE'])
            if result['returncode'] == 0:
                page_size = int(result['stdout'].strip())
                return f"{page_size} bytes ({page_size // 1024}K)"
            return "Unknown"
        except:
            return "Unknown"
    
    async def _check_kernel_messages(self) -> List[Dict[str, str]]:
        """Check recent kernel messages for errors"""
        try:
            result = await self._run_command(['dmesg', '-T', '-l', 'err,crit,alert,emerg'])
            if result['returncode'] == 0:
                messages = []
                for line in result['stdout'].split('\n')[-20:]:  # Last 20 error messages
                    if line.strip():
                        messages.append({
                            'message': line.strip(),
                            'severity': 'error'
                        })
                return messages
            return []
        except:
            return []
    
    async def _check_loaded_modules(self) -> Dict[str, Any]:
        """Check loaded kernel modules"""
        try:
            result = await self._run_command(['lsmod'])
            if result['returncode'] == 0:
                lines = result['stdout'].split('\n')[1:]  # Skip header
                modules = {}
                asahi_modules = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            module_name = parts[0]
                            size = parts[1]
                            used_by = parts[2] if len(parts) > 2 else "0"
                            
                            modules[module_name] = {
                                'size': size,
                                'used_by_count': used_by
                            }
                            
                            # Check for Asahi-specific modules
                            if any(keyword in module_name.lower() for keyword in ['apple', 'asahi', 'macsmc', 'm1']):
                                asahi_modules.append(module_name)
                
                return {
                    'total_modules': len(modules),
                    'asahi_modules': asahi_modules,
                    'critical_missing': await self._check_missing_critical_modules()
                }
            return {}
        except:
            return {}
    
    async def _check_missing_critical_modules(self) -> List[str]:
        """Check for missing critical modules"""
        critical_modules = [
            'apple_mfi_fastcharge',
            'macsmc',
            'apple_smc',
            'asahi_wlan',
        ]
        
        missing = []
        try:
            result = await self._run_command(['lsmod'])
            if result['returncode'] == 0:
                loaded_modules = result['stdout'].lower()
                for module in critical_modules:
                    if module.lower() not in loaded_modules:
                        missing.append(module)
        except:
            pass
        
        return missing
    
    async def _get_kernel_parameters(self) -> str:
        """Get kernel boot parameters"""
        try:
            with open('/proc/cmdline', 'r') as f:
                return f.read().strip()
        except:
            return "Unknown"
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage and identify issues"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_memory': memory.total,
                'available_memory': memory.available,
                'used_memory': memory.used,
                'memory_percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent,
                'memory_pressure': memory.percent > 90,
                'swap_pressure': swap.percent > 50 if swap.total > 0 else False,
                'oom_killer_activity': await self._check_oom_activity(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _check_oom_activity(self) -> List[str]:
        """Check for Out of Memory killer activity"""
        try:
            result = await self._run_command(['dmesg', '-T'])
            if result['returncode'] == 0:
                oom_lines = []
                for line in result['stdout'].split('\n'):
                    if 'killed process' in line.lower() or 'out of memory' in line.lower():
                        oom_lines.append(line.strip())
                return oom_lines[-10:]  # Last 10 OOM events
            return []
        except:
            return []
    
    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage and health"""
        try:
            disk_info = {}
            
            # Get disk usage for all mounted filesystems
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100,
                        'critical': (usage.used / usage.total) > 0.9
                    }
                except PermissionError:
                    continue
            
            # Check for disk errors
            disk_errors = await self._check_disk_errors()
            
            # Check SMART status if available
            smart_status = await self._check_smart_status()
            
            return {
                'partitions': disk_info,
                'disk_errors': disk_errors,
                'smart_status': smart_status,
                'apfs_issues': await self._check_apfs_issues()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _check_disk_errors(self) -> List[str]:
        """Check for disk-related errors in logs"""
        try:
            result = await self._run_command(['dmesg', '-T'])
            if result['returncode'] == 0:
                error_patterns = ['I/O error', 'disk error', 'ata error', 'nvme error', 'blk_update_request']
                errors = []
                
                for line in result['stdout'].split('\n'):
                    line_lower = line.lower()
                    if any(pattern.lower() in line_lower for pattern in error_patterns):
                        errors.append(line.strip())
                
                return errors[-10:]  # Last 10 disk errors
            return []
        except:
            return []
    
    async def _check_smart_status(self) -> Dict[str, Any]:
        """Check SMART status of drives"""
        try:
            # Try to get SMART info using smartctl
            result = await self._run_command(['smartctl', '--scan'])
            if result['returncode'] == 0:
                smart_info = {}
                for line in result['stdout'].split('\n'):
                    if line.strip() and not line.startswith('#'):
                        device = line.split()[0]
                        status_result = await self._run_command(['smartctl', '-H', device])
                        if status_result['returncode'] == 0:
                            smart_info[device] = 'PASSED' if 'PASSED' in status_result['stdout'] else 'FAILED'
                return smart_info
            return {}
        except:
            return {}
    
    async def _check_apfs_issues(self) -> List[str]:
        """Check for APFS-related issues specific to Asahi"""
        issues = []
        try:
            # Check for APFS partition corruption warnings
            result = await self._run_command(['dmesg'])
            if result['returncode'] == 0:
                for line in result['stdout'].split('\n'):
                    if 'apfs' in line.lower() and ('error' in line.lower() or 'corrupt' in line.lower()):
                        issues.append(line.strip())
            
            # Check disk space for macOS compatibility (38GB requirement)
            for partition in psutil.disk_partitions():
                if 'apfs' in partition.fstype.lower():
                    usage = psutil.disk_usage(partition.mountpoint)
                    free_gb = usage.free / (1024**3)
                    if free_gb < 38:
                        issues.append(f"APFS partition {partition.mountpoint} has less than 38GB free (macOS requirement)")
        except:
            pass
        
        return issues
    
    async def _check_boot_issues(self) -> Dict[str, Any]:
        """Check for boot-related issues"""
        return {
            'boot_time': await self._get_boot_time(),
            'failed_services': await self._get_failed_services(),
            'boot_errors': await self._check_boot_errors(),
            'm1n1_status': await self._check_m1n1_status(),
        }
    
    async def _get_boot_time(self) -> str:
        """Get last boot time"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            return boot_time.isoformat()
        except:
            return "Unknown"
    
    async def _get_failed_services(self) -> List[str]:
        """Get list of failed systemd services"""
        try:
            result = await self._run_command(['systemctl', '--failed', '--no-legend'])
            if result['returncode'] == 0:
                failed_services = []
                for line in result['stdout'].split('\n'):
                    if line.strip():
                        service_name = line.split()[0]
                        failed_services.append(service_name)
                return failed_services
            return []
        except:
            return []
    
    async def _check_boot_errors(self) -> List[str]:
        """Check for boot-related errors"""
        try:
            # Check journal for boot errors
            result = await self._run_command(['journalctl', '-b', '-p', 'err', '--no-pager', '-n', '50'])
            if result['returncode'] == 0:
                errors = []
                for line in result['stdout'].split('\n'):
                    if line.strip() and any(keyword in line.lower() for keyword in ['boot', 'init', 'failed', 'error']):
                        errors.append(line.strip())
                return errors
            return []
        except:
            return []
    
    async def _check_m1n1_status(self) -> Dict[str, str]:
        """Check m1n1 bootloader status"""
        status = {}
        try:
            # m1n1 is the bootloader for Asahi Linux
            # Check if m1n1 version info is available
            if Path('/sys/firmware/devicetree/base/chosen/asahi,efi-system-table').exists():
                status['m1n1_present'] = 'Yes'
            else:
                status['m1n1_present'] = 'Unknown'
            
            # Try to get version info from dmesg
            result = await self._run_command(['dmesg'])
            if result['returncode'] == 0:
                for line in result['stdout'].split('\n'):
                    if 'm1n1' in line.lower():
                        status['m1n1_info'] = line.strip()
                        break
        except:
            status['error'] = 'Unable to check m1n1 status'
        
        return status
    
    async def _check_display_issues(self) -> Dict[str, Any]:
        """Check for display and graphics issues"""
        return {
            'display_servers': await self._check_display_servers(),
            'graphics_drivers': await self._check_graphics_drivers(),
            'refresh_rate_issues': await self._check_refresh_rate_issues(),
            'hdmi_support': await self._check_hdmi_support(),
        }
    
    async def _check_display_servers(self) -> Dict[str, bool]:
        """Check running display servers"""
        display_servers = {}
        try:
            # Check for Wayland
            result = await self._run_command(['pgrep', '-f', 'wayland'])
            display_servers['wayland'] = result['returncode'] == 0
            
            # Check for X11
            result = await self._run_command(['pgrep', '-f', 'Xorg|X11'])
            display_servers['x11'] = result['returncode'] == 0
            
        except:
            pass
        return display_servers
    
    async def _check_graphics_drivers(self) -> Dict[str, Any]:
        """Check graphics driver status"""
        try:
            graphics_info = {}
            
            # Check for DRM devices
            result = await self._run_command(['ls', '/dev/dri/'])
            if result['returncode'] == 0:
                graphics_info['drm_devices'] = result['stdout'].strip().split('\n')
            
            # Check loaded graphics modules
            result = await self._run_command(['lsmod'])
            if result['returncode'] == 0:
                graphics_modules = []
                for line in result['stdout'].split('\n'):
                    if any(gpu in line.lower() for gpu in ['apple', 'asahi', 'drm', 'gpu']):
                        graphics_modules.append(line.split()[0])
                graphics_info['loaded_modules'] = graphics_modules
            
            return graphics_info
        except:
            return {}
    
    async def _check_refresh_rate_issues(self) -> List[str]:
        """Check for ProMotion/refresh rate issues"""
        issues = []
        try:
            # Check dmesg for display-related issues
            result = await self._run_command(['dmesg'])
            if result['returncode'] == 0:
                for line in result['stdout'].split('\n'):
                    if any(keyword in line.lower() for keyword in ['promotion', 'refresh', 'display', 'black screen']):
                        if any(error in line.lower() for error in ['error', 'failed', 'warning']):
                            issues.append(line.strip())
        except:
            pass
        return issues
    
    async def _check_hdmi_support(self) -> Dict[str, str]:
        """Check HDMI output support"""
        try:
            # Check for connected displays
            if os.path.exists('/sys/class/drm'):
                connectors = []
                for item in os.listdir('/sys/class/drm'):
                    if 'HDMI' in item:
                        status_path = f'/sys/class/drm/{item}/status'
                        if os.path.exists(status_path):
                            with open(status_path, 'r') as f:
                                status = f.read().strip()
                                connectors.append({item: status})
                
                return {'hdmi_connectors': connectors}
            return {}
        except:
            return {}
    
    async def _check_power_management(self) -> Dict[str, Any]:
        """Check power management and battery status"""
        power_info = {}
        try:
            # Check battery status
            battery = psutil.sensors_battery()
            if battery:
                power_info['battery'] = {
                    'percent': battery.percent,
                    'plugged': battery.power_plugged,
                    'time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
            
            # Check CPU frequency scaling
            if psutil.cpu_freq():
                power_info['cpu_freq'] = {
                    'current': psutil.cpu_freq().current,
                    'min': psutil.cpu_freq().min,
                    'max': psutil.cpu_freq().max
                }
            
            # Check power profiles
            result = await self._run_command(['cat', '/sys/firmware/acpi/platform_profile'])
            if result['returncode'] == 0:
                power_info['power_profile'] = result['stdout'].strip()
            
        except:
            pass
        return power_info
    
    async def _check_thermal_status(self) -> Dict[str, Any]:
        """Check thermal sensors and temperature"""
        thermal_info = {}
        try:
            # Check thermal zones
            if os.path.exists('/sys/class/thermal'):
                thermal_zones = {}
                for zone in os.listdir('/sys/class/thermal'):
                    if zone.startswith('thermal_zone'):
                        temp_path = f'/sys/class/thermal/{zone}/temp'
                        type_path = f'/sys/class/thermal/{zone}/type'
                        
                        if os.path.exists(temp_path) and os.path.exists(type_path):
                            with open(temp_path, 'r') as f:
                                temp = int(f.read().strip()) / 1000  # Convert to Celsius
                            with open(type_path, 'r') as f:
                                zone_type = f.read().strip()
                            
                            thermal_zones[zone] = {
                                'type': zone_type,
                                'temperature': temp,
                                'critical': temp > 80  # Flag if over 80°C
                            }
                
                thermal_info['thermal_zones'] = thermal_zones
            
            # Check for thermal throttling
            result = await self._run_command(['dmesg'])
            if result['returncode'] == 0:
                throttling_events = []
                for line in result['stdout'].split('\n'):
                    if 'thermal' in line.lower() and 'throttl' in line.lower():
                        throttling_events.append(line.strip())
                thermal_info['throttling_events'] = throttling_events[-5:]  # Last 5 events
            
        except:
            pass
        return thermal_info
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """Check network connectivity and WiFi status"""
        network_info = {}
        try:
            # Check network interfaces
            interfaces = psutil.net_if_addrs()
            interface_stats = psutil.net_if_stats()
            
            network_info['interfaces'] = {}
            for interface, addresses in interfaces.items():
                stats = interface_stats.get(interface, None)
                network_info['interfaces'][interface] = {
                    'addresses': [{'family': addr.family.name, 'address': addr.address} for addr in addresses],
                    'is_up': stats.isup if stats else False,
                    'speed': stats.speed if stats else 0
                }
            
            # Check WiFi status (Asahi-specific)
            wifi_info = await self._check_wifi_status()
            network_info['wifi'] = wifi_info
            
            # Check connectivity
            network_info['connectivity'] = await self._check_connectivity()
            
        except:
            pass
        return network_info
    
    async def _check_wifi_status(self) -> Dict[str, Any]:
        """Check WiFi status and Asahi WiFi driver"""
        wifi_info = {}
        try:
            # Check if Asahi WiFi driver is loaded
            result = await self._run_command(['lsmod'])
            if result['returncode'] == 0:
                wifi_drivers = []
                for line in result['stdout'].split('\n'):
                    if any(wifi in line.lower() for wifi in ['brcm', 'asahi_wlan', 'wlan', '80211']):
                        wifi_drivers.append(line.split()[0])
                wifi_info['loaded_drivers'] = wifi_drivers
            
            # Check wireless interfaces
            result = await self._run_command(['iwconfig'])
            if result['returncode'] == 0:
                wifi_info['wireless_interfaces'] = result['stdout']
            
            # Check WiFi connection status
            result = await self._run_command(['nmcli', 'dev', 'wifi', 'list'])
            if result['returncode'] == 0:
                wifi_info['available_networks'] = len(result['stdout'].split('\n')) - 1
        except:
            pass
        return wifi_info
    
    async def _check_connectivity(self) -> Dict[str, bool]:
        """Check internet connectivity"""
        connectivity = {}
        try:
            # Check DNS resolution
            result = await self._run_command(['nslookup', 'google.com'])
            connectivity['dns'] = result['returncode'] == 0
            
            # Check internet connectivity
            result = await self._run_command(['ping', '-c', '1', '8.8.8.8'])
            connectivity['internet'] = result['returncode'] == 0
            
        except:
            connectivity = {'dns': False, 'internet': False}
        return connectivity
    
    async def _check_systemd_services(self) -> Dict[str, Any]:
        """Check systemd service status"""
        try:
            # Get all services
            result = await self._run_command(['systemctl', 'list-units', '--type=service', '--all', '--no-legend'])
            if result['returncode'] == 0:
                services = {
                    'total': 0,
                    'active': 0,
                    'failed': 0,
                    'inactive': 0,
                    'failed_services': []
                }
                
                for line in result['stdout'].split('\n'):
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            services['total'] += 1
                            state = parts[2]
                            
                            if state == 'active':
                                services['active'] += 1
                            elif state == 'failed':
                                services['failed'] += 1
                                services['failed_services'].append(parts[0])
                            else:
                                services['inactive'] += 1
                
                return services
            return {}
        except:
            return {}
    
    async def _check_asahi_specific_issues(self) -> Dict[str, Any]:
        """Check for Asahi Linux specific issues"""
        asahi_issues = {
            'page_size_compatibility': await self._check_page_size_issues(),
            'rust_jemalloc_issues': await self._check_rust_issues(),
            'macos_compatibility': await self._check_macos_compatibility(),
            'upstream_kernel_status': await self._check_upstream_status(),
        }
        return asahi_issues
    
    async def _check_page_size_issues(self) -> List[str]:
        """Check for 16K page size compatibility issues"""
        issues = []
        try:
            # Check if page size is 16K
            result = await self._run_command(['getconf', 'PAGESIZE'])
            if result['returncode'] == 0:
                page_size = int(result['stdout'].strip())
                if page_size == 16384:  # 16K
                    issues.append("16K page size detected - some software may have compatibility issues")
                    
                    # Check for known problematic software
                    problematic_software = ['rust', 'cargo', 'rustc']
                    for software in problematic_software:
                        result = await self._run_command(['which', software])
                        if result['returncode'] == 0:
                            issues.append(f"{software} detected - may have jemalloc/libunwind issues with 16K pages")
        except:
            pass
        return issues
    
    async def _check_rust_issues(self) -> List[str]:
        """Check for Rust/jemalloc issues with 16K pages"""
        issues = []
        try:
            # Check if Rust is installed from Arch repos (problematic)
            result = await self._run_command(['pacman', '-Q', 'rust'])
            if result['returncode'] == 0:
                issues.append("Rust from Arch repos detected - may not work with 16K pages. Consider rustup installation.")
                
            # Check for cargo issues
            result = await self._run_command(['cargo', '--version'])
            if result['returncode'] != 0:
                issues.append("Cargo not working - likely due to 16K page size compatibility")
                
        except:
            pass
        return issues
    
    async def _check_macos_compatibility(self) -> Dict[str, Any]:
        """Check macOS compatibility requirements"""
        compat_info = {}
        try:
            # Check disk space for macOS (38GB requirement)
            total_free = 0
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_free += usage.free
                except:
                    continue
            
            free_gb = total_free / (1024**3)
            compat_info['macos_space_requirement'] = {
                'required_gb': 38,
                'available_gb': free_gb,
                'sufficient': free_gb >= 38
            }
            
            # Check if macOS is still present
            macos_present = False
            for partition in psutil.disk_partitions():
                if 'apfs' in partition.fstype.lower():
                    macos_present = True
                    break
            
            compat_info['macos_present'] = macos_present
            
        except:
            pass
        return compat_info
    
    async def _check_upstream_status(self) -> Dict[str, str]:
        """Check status of upstream kernel patches"""
        try:
            # This would typically check against a known list of patches
            # For now, just check kernel version and note downstream status
            kernel_version = platform.release()
            
            status = {
                'kernel_version': kernel_version,
                'is_downstream': '16k' in kernel_version.lower() or 'asahi' in kernel_version.lower(),
                'patches_status': 'Using downstream kernel with Asahi-specific patches'
            }
            
            if status['is_downstream']:
                status['note'] = "Running Asahi downstream kernel - some features may not be in upstream"
            
            return status
        except:
            return {'error': 'Unable to determine kernel status'}
    
    async def _run_command(self, cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run a command and return results"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            }
        except asyncio.TimeoutError:
            return {'returncode': -1, 'error': 'Command timeout'}
        except Exception as e:
            return {'returncode': -1, 'error': str(e)}
    
    async def scan_applications(self) -> Dict[str, Any]:
        """Scan installed applications and their health"""
        # Implementation for application scanning
        return {'placeholder': 'Application scan not yet implemented'}
    
    async def scan_configurations(self) -> Dict[str, Any]:
        """Scan system configurations"""
        # Implementation for configuration scanning
        return {'placeholder': 'Configuration scan not yet implemented'}
    
    async def scan_repositories(self) -> Dict[str, Any]:
        """Scan package repositories"""
        # Implementation for repository scanning  
        return {'placeholder': 'Repository scan not yet implemented'}
    
    async def scan_logs(self) -> Dict[str, Any]:
        """Scan system logs for issues"""
        # Implementation for log scanning
        return {'placeholder': 'Log scan not yet implemented'}
    
    async def scan_hardware(self) -> Dict[str, Any]:
        """Scan hardware status"""
        # Implementation for hardware scanning
        return {'placeholder': 'Hardware scan not yet implemented'}
    
    async def cleanup(self):
        """Cleanup resources"""
        pass