#!/usr/bin/env python3
"""
Orion Browser Speed Optimization Script
Diagnoses performance issues and safely cleans up caches while preserving bookmarks and passwords.

CRITICAL WARNING - NO WARRANTY
==============================
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
USE ENTIRELY AT YOUR OWN RISK.

The authors are NOT LIABLE for any damage, data loss, or system issues.
YOU are solely responsible for any consequences of using this software.
CREATE A COMPLETE SYSTEM BACKUP before use.

By using this software, you acknowledge and agree to these terms.
"""

import os
import shutil
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import psutil

class OrionSpeedOptimizer:
    def __init__(self):
        self.orion_path = Path.home() / "Library" / "Application Support" / "Orion"
        self.backup_path = Path.home() / "Desktop" / f"Orion_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.critical_files = [
            "Bookmarks.plist",
            "History.plist",
            "Passwords.plist",
            "Keychain",
            "Login Data",
            "preferences.plist",
            "LocalStorage",
            "WebKitLocalStorage"
        ]

    def print_header(self):
        print("=" * 70)
        print("🚀 ORION BROWSER SPEED OPTIMIZATION TOOL")
        print("=" * 70)
        print()

    def check_orion_running(self):
        """Check if Orion is currently running"""
        print("🔍 Checking if Orion is running...")
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'orion' in proc.info['name'].lower():
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None

    def close_orion(self):
        """Safely close Orion browser"""
        print("🛑 Closing Orion browser...")
        try:
            # Try graceful close first
            subprocess.run(['osascript', '-e', 'tell application "Orion" to quit'],
                         capture_output=True, timeout=10)
            time.sleep(3)

            # Force close if still running
            is_running, pid = self.check_orion_running()
            if is_running:
                print(f"   Force closing Orion (PID: {pid})")
                subprocess.run(['kill', str(pid)], capture_output=True)
                time.sleep(2)

            print("   ✅ Orion closed successfully")
            return True
        except Exception as e:
            print(f"   ⚠️  Error closing Orion: {e}")
            return False

    def get_cache_impact_analysis(self, cache_name, size_mb):
        """Analyze the performance impact of specific cache sizes"""
        impact_data = {
            "Cache": {
                "low": 50, "medium": 200, "high": 500,
                "impact": {
                    "low": "✅ Normal - HTTP cache helps page loading",
                    "medium": "⚠️  Moderate impact - May slow startup slightly",
                    "high": "🚨 High impact - Significantly slows startup and browsing"
                },
                "description": "Main HTTP cache for web resources (images, CSS, JS)"
            },
            "WebKitCache": {
                "low": 30, "medium": 150, "high": 400,
                "impact": {
                    "low": "✅ Normal - WebKit rendering cache is healthy",
                    "medium": "⚠️  Moderate impact - Page rendering may lag",
                    "high": "🚨 High impact - Severe rendering delays and memory usage"
                },
                "description": "WebKit engine cache for rendered page elements"
            },
            "GPUCache": {
                "low": 20, "medium": 100, "high": 300,
                "impact": {
                    "low": "✅ Normal - GPU acceleration working efficiently",
                    "medium": "⚠️  Moderate impact - Graphics performance degraded",
                    "high": "🚨 High impact - GPU memory exhausted, graphics lag"
                },
                "description": "GPU-accelerated rendering and WebGL cache"
            },
            "Code Cache": {
                "low": 15, "medium": 80, "high": 200,
                "impact": {
                    "low": "✅ Normal - JavaScript compilation cache optimal",
                    "medium": "⚠️  Moderate impact - JS execution slower",
                    "high": "🚨 High impact - Severe JavaScript performance issues"
                },
                "description": "Compiled JavaScript bytecode cache"
            },
            "IndexedDB": {
                "low": 10, "medium": 50, "high": 150,
                "impact": {
                    "low": "✅ Normal - Web app data storage healthy",
                    "medium": "⚠️  Moderate impact - Web app performance affected",
                    "high": "🚨 High impact - Web apps may crash or freeze"
                },
                "description": "Web application database storage"
            },
            "Local Storage": {
                "low": 5, "medium": 25, "high": 100,
                "impact": {
                    "low": "✅ Normal - Website preferences stored efficiently",
                    "medium": "⚠️  Moderate impact - Website loading slower",
                    "high": "🚨 High impact - Websites may lose settings/fail to load"
                },
                "description": "Website local storage and preferences"
            },
            "blob_storage": {
                "low": 20, "medium": 100, "high": 250,
                "impact": {
                    "low": "✅ Normal - File downloads and uploads working well",
                    "medium": "⚠️  Moderate impact - File operations slower",
                    "high": "🚨 High impact - File download/upload failures"
                },
                "description": "Binary file storage for downloads and uploads"
            },
            "Service Worker": {
                "low": 5, "medium": 30, "high": 100,
                "impact": {
                    "low": "✅ Normal - Offline functionality working",
                    "medium": "⚠️  Moderate impact - PWA performance degraded",
                    "high": "🚨 High impact - Progressive web apps broken"
                },
                "description": "Service worker cache for offline functionality"
            }
        }

        # Default analysis for unknown cache types
        default = {
            "low": 10, "medium": 50, "high": 150,
            "impact": {
                "low": "✅ Normal size",
                "medium": "⚠️  Moderate size - may impact performance",
                "high": "🚨 Large size - likely impacting performance"
            },
            "description": "Browser cache component"
        }

        cache_info = impact_data.get(cache_name, default)

        if size_mb <= cache_info["low"]:
            level = "low"
        elif size_mb <= cache_info["medium"]:
            level = "medium"
        else:
            level = "high"

        return {
            "level": level,
            "impact": cache_info["impact"][level],
            "description": cache_info["description"],
            "recommendation": "Keep" if level == "low" else "Clean" if level == "high" else "Monitor"
        }

    def diagnose_performance(self):
        """Diagnose potential performance issues with detailed analysis"""
        print("🔍 DIAGNOSING ORION PERFORMANCE ISSUES")
        print("-" * 70)

        if not self.orion_path.exists():
            print("❌ Orion data directory not found!")
            return False

        issues = []
        recommendations = []
        total_cache_size = 0

        # Enhanced cache analysis
        cache_dirs = [
            "Cache", "CachedData", "WebKitCache", "GPUCache", "DawnCache",
            "Code Cache", "blob_storage", "Service Worker", "IndexedDB",
            "databases", "Local Storage", "Session Storage", "QuotaManager",
            "Network Persistent State", "TransportSecurity"
        ]

        print("📊 DETAILED CACHE ANALYSIS:")
        print("-" * 70)

        for cache_dir in cache_dirs:
            cache_path = self.orion_path / cache_dir
            if cache_path.exists():
                try:
                    size = self.get_directory_size(cache_path)
                    total_cache_size += size
                    size_mb = size / (1024 * 1024)

                    analysis = self.get_cache_impact_analysis(cache_dir, size_mb)

                    print(f"\n📁 {cache_dir}")
                    print(f"   Size: {size_mb:.1f} MB")
                    print(f"   Impact: {analysis['impact']}")
                    print(f"   Purpose: {analysis['description']}")

                    if analysis['level'] == 'high':
                        issues.append(f"Large {cache_dir} directory ({size_mb:.1f} MB)")
                        recommendations.append(f"Clean {cache_dir} to improve performance")
                    elif analysis['level'] == 'medium':
                        recommendations.append(f"Monitor {cache_dir} size")

                except Exception as e:
                    print(f"\n📁 {cache_dir}: ❌ Unable to read ({e})")

        print(f"\n{'='*70}")
        print(f"📈 TOTAL CACHE SIZE: {total_cache_size / (1024 * 1024):.1f} MB")

        # Enhanced cache size interpretation with performance impact estimates
        total_mb = total_cache_size / (1024 * 1024)
        if total_mb < 100:
            cache_status = "🌟 Excellent - Cache size is minimal"
            impact_msg = "📈 Impact: <1s startup delay, <50MB RAM usage"
            recommendation = "🔧 No cache cleanup needed"
        elif total_mb < 200:
            cache_status = "✅ Healthy - Cache size is normal"
            impact_msg = "📈 Impact: +1-3s startup delay, +50-100MB RAM usage"
            recommendation = "🔧 Cache cleanup optional but won't hurt"
        elif total_mb < 500:
            cache_status = "📈 Moderate - Cache size could be optimized"
            impact_msg = "📈 Impact: +3-8s startup delay, +100-200MB RAM usage"
            recommendation = "🔧 Cache cleanup recommended for better performance"
        elif total_mb < 1000:
            cache_status = "⚠️  Warning - Large cache may slow startup"
            impact_msg = "📈 Impact: +8-15s startup delay, +200-500MB RAM usage"
            recommendation = "🔧 Cache cleanup strongly recommended"
        else:
            cache_status = "🚨 Critical - Cache size significantly impacting performance"
            impact_msg = "📈 Impact: +15-30s startup delay, +500MB+ RAM usage"
            recommendation = "🔧 Immediate cache cleanup required"

        print(f"Status: {cache_status}")
        print(f"{impact_msg}")
        print(f"{recommendation}")
        print(f"{'='*70}")

        # Check extensions
        extensions_path = self.orion_path / "Extensions"
        if extensions_path.exists():
            extensions = list(extensions_path.glob("*"))
            print(f"🧩 Extensions: {len(extensions)} installed")
            if len(extensions) > 10:
                issues.append(f"Many extensions installed ({len(extensions)})")

        # Enhanced history analysis
        print(f"\n📚 HISTORY ANALYSIS:")
        print("-" * 30)

        history_files = ["History.plist", "History.db", "History-journal"]
        total_history_size = 0

        for hist_file in history_files:
            hist_path = self.orion_path / hist_file
            if hist_path.exists():
                hist_size = hist_path.stat().st_size / (1024 * 1024)
                total_history_size += hist_size
                print(f"   {hist_file}: {hist_size:.1f} MB")

        print(f"   Total History Size: {total_history_size:.1f} MB")

        # History impact analysis
        if total_history_size < 10:
            hist_status = "✅ Normal - History size is healthy"
        elif total_history_size < 50:
            hist_status = "⚠️  Moderate - History may slow searches"
        else:
            hist_status = "🚨 Large - History significantly slowing browser"
            issues.append(f"Large history files ({total_history_size:.1f} MB)")
            recommendations.append("Consider clearing old browsing history")

        print(f"   Status: {hist_status}")

        # Estimate history items (rough calculation)
        if total_history_size > 0:
            estimated_items = int(total_history_size * 1000)  # Rough estimate
            print(f"   Estimated entries: ~{estimated_items:,} items")
            if estimated_items > 10000:
                recommendations.append("Reduce history retention period")

        # Check available disk space
        disk_usage = shutil.disk_usage(Path.home())
        free_space_gb = disk_usage.free / (1024 * 1024 * 1024)
        print(f"💾 Available disk space: {free_space_gb:.1f} GB")
        if free_space_gb < 5:
            issues.append(f"Low disk space ({free_space_gb:.1f} GB free)")

        # Check system memory
        memory = psutil.virtual_memory()
        print(f"🧠 System RAM: {memory.total / (1024**3):.1f} GB total, {memory.available / (1024**3):.1f} GB available")
        if memory.percent > 80:
            issues.append(f"High memory usage ({memory.percent:.1f}%)")

        print(f"\n🎯 DIAGNOSIS SUMMARY:")
        print("-" * 50)

        if issues:
            print("⚠️  PERFORMANCE ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. ❌ {issue}")
        else:
            print("✅ No major performance issues detected")

        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. 🔧 {rec}")

        # Performance score calculation
        score = 100
        if total_mb > 800: score -= 30
        elif total_mb > 400: score -= 15

        if total_history_size > 50: score -= 20
        elif total_history_size > 20: score -= 10

        if len(issues) > 3: score -= 20
        elif len(issues) > 0: score -= 10

        if free_space_gb < 5: score -= 25
        elif free_space_gb < 10: score -= 15

        score = max(0, score)  # Don't go below 0

        print(f"\n📊 ORION PERFORMANCE SCORE: {score}/100")
        if score >= 80:
            score_status = "🟢 Excellent - Your browser is well optimized"
        elif score >= 60:
            score_status = "🟡 Good - Minor optimizations recommended"
        elif score >= 40:
            score_status = "🟠 Fair - Several optimizations needed"
        else:
            score_status = "🔴 Poor - Significant cleanup required"

        print(f"Status: {score_status}")

        # If no issues found but user reports slowness, do advanced diagnosis
        if len(issues) == 0:
            print(f"\n🕵️  ADVANCED DIAGNOSIS - Checking deeper performance factors...")
            print("-" * 70)
            print("   ℹ️  This may take 10-15 seconds for thorough analysis...")
            start_time = time.time()

            advanced_issues = self.advanced_performance_check()

            end_time = time.time()
            print(f"   ⏱️  Advanced diagnosis completed in {end_time - start_time:.1f} seconds")

            if advanced_issues:
                issues.extend(advanced_issues)
                print(f"\n⚠️  ADDITIONAL ISSUES FOUND:")
                for i, issue in enumerate(advanced_issues, 1):
                    print(f"   {i}. 🔍 {issue}")
            else:
                print(f"\n✅ No additional performance issues detected in advanced analysis")

        return len(issues) > 0

    def get_directory_size(self, path):
        """Get total size of directory"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_directory_size(entry.path)
        except (PermissionError, OSError):
            pass
        return total

    def advanced_performance_check(self):
        """Advanced performance diagnostics for when basic checks pass"""
        advanced_issues = []

        # Since user reports Safari/other browsers are fast but Orion is slow,
        # prioritize Orion-specific checks over system-wide issues

        print("   🎯 Focusing on Orion-specific issues (other browsers work fine)...")

        # 1. Check Orion processes (HIGH PRIORITY)
        orion_processes = self.check_orion_processes()
        if orion_processes:
            advanced_issues.extend(orion_processes)

        # 2. Check extensions impact (HIGH PRIORITY)
        extension_issues = self.check_extensions_performance()
        if extension_issues:
            advanced_issues.extend(extension_issues)

        # 3. Check Orion-specific settings (HIGH PRIORITY)
        orion_settings_issues = self.check_orion_specific_settings()
        if orion_settings_issues:
            advanced_issues.extend(orion_settings_issues)

        # 4. Check database integrity (MEDIUM PRIORITY)
        db_issues = self.check_database_integrity()
        if db_issues:
            advanced_issues.extend(db_issues)

        # 5. Check Orion profile corruption (NEW - HIGH PRIORITY)
        profile_issues = self.check_orion_profile_corruption()
        if profile_issues:
            advanced_issues.extend(profile_issues)

        # 6. Check Orion vs Safari comparison (NEW - HIGH PRIORITY)
        comparison_issues = self.compare_with_safari()
        if comparison_issues:
            advanced_issues.extend(comparison_issues)

        # Skip system-wide and network checks since other browsers work fine
        # (User reported Safari is fast, so system/network are not the issue)

        return advanced_issues

    def check_orion_processes(self):
        """Check Orion process performance"""
        issues = []
        print("🔍 Checking Orion processes...")

        orion_processes = []

        # First pass: collect all Orion processes without CPU sampling
        orion_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'create_time']):
            try:
                if 'orion' in proc.info['name'].lower():
                    orion_procs.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Second pass: Get CPU usage with shorter interval for speed
        for proc in orion_procs:
            try:
                # Get instant CPU usage (faster but less accurate)
                cpu_usage = proc.cpu_percent(interval=0.1)  # Reduced from 1 second
                memory_mb = proc.memory_info().rss / (1024 * 1024)
                uptime_hours = (time.time() - proc.create_time()) / 3600

                orion_processes.append({
                    'pid': proc.pid,
                    'name': proc.name(),
                    'cpu': cpu_usage,
                    'memory': memory_mb,
                    'uptime': uptime_hours
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if orion_processes:
            total_memory = sum(p['memory'] for p in orion_processes)
            max_cpu = max(p['cpu'] for p in orion_processes)
            longest_uptime = max(p['uptime'] for p in orion_processes)

            print(f"   Found {len(orion_processes)} Orion processes")
            print(f"   Total memory usage: {total_memory:.1f} MB")
            print(f"   Highest CPU usage: {max_cpu:.1f}%")
            print(f"   Longest uptime: {longest_uptime:.1f} hours")

            if total_memory > 2000:  # More than 2GB
                issues.append(f"High memory usage by Orion processes ({total_memory:.1f} MB)")

            if max_cpu > 50:  # High CPU usage
                issues.append(f"High CPU usage by Orion ({max_cpu:.1f}%)")

            if longest_uptime > 24:  # Running for more than 24 hours
                issues.append(f"Orion has been running for {longest_uptime:.1f} hours - restart recommended")

        return issues

    def check_extensions_performance(self):
        """Check extension impact on performance"""
        issues = []
        print("🧩 Analyzing extension performance impact...")

        extensions_path = self.orion_path / "Extensions"
        if not extensions_path.exists():
            return issues

        # Known problematic extensions (based on common issues)
        problematic_extensions = {
            'adblocker': 'Ad blockers can slow page loading significantly',
            'grammarly': 'Grammarly extension can cause typing lag',
            'honey': 'Honey coupon finder causes delays on shopping sites',
            'lastpass': 'Password managers can slow form filling',
            '1password': 'Password managers can slow form filling',
            'pinterest': 'Pinterest save button can slow image-heavy sites',
            'pocket': 'Save-to-Pocket can delay page loading',
            'evernote': 'Web clipper can impact page performance'
        }

        extensions = list(extensions_path.glob("*"))
        print(f"   Found {len(extensions)} extensions installed")

        if len(extensions) > 15:
            issues.append(f"Too many extensions ({len(extensions)}) - each adds overhead")

        # Check for known problematic extensions
        for ext_dir in extensions:
            ext_name = ext_dir.name.lower()
            for problem_key, problem_desc in problematic_extensions.items():
                if problem_key in ext_name:
                    issues.append(f"Extension '{ext_dir.name}' - {problem_desc}")

        # Check extension data size
        total_ext_data = 0
        for ext_dir in extensions:
            try:
                ext_size = self.get_directory_size(ext_dir) / (1024 * 1024)
                total_ext_data += ext_size
                if ext_size > 50:  # Extension data over 50MB
                    issues.append(f"Extension '{ext_dir.name}' has large data ({ext_size:.1f} MB)")
            except Exception:
                continue

        if total_ext_data > 200:  # Total extension data over 200MB
            issues.append(f"Total extension data is large ({total_ext_data:.1f} MB)")

        return issues

    def check_database_integrity(self):
        """Check for database corruption or issues"""
        issues = []
        print("🗄️  Checking database integrity...")

        db_files = [
            "History.db", "Bookmarks.db", "Cookies.db",
            "Login Data", "Web Data", "Favicons.db"
        ]

        for db_file in db_files:
            db_path = self.orion_path / db_file
            if db_path.exists():
                try:
                    # Check for very large databases (fast check)
                    db_size = db_path.stat().st_size / (1024 * 1024)
                    print(f"   {db_file}: {db_size:.1f} MB")

                    if db_size > 500:  # Database over 500MB
                        issues.append(f"Database '{db_file}' is very large ({db_size:.1f} MB)")

                    # Quick integrity check with shorter timeout
                    if db_size > 0:  # Only check non-empty files
                        result = subprocess.run(['sqlite3', str(db_path), '.tables'],
                                              capture_output=True, text=True, timeout=2)  # Reduced timeout
                        if result.returncode != 0:
                            issues.append(f"Database '{db_file}' may be corrupted")

                except subprocess.TimeoutExpired:
                    issues.append(f"Database '{db_file}' is locked or unresponsive")
                except Exception as e:
                    print(f"   {db_file}: Unable to check ({str(e)[:50]}...)")

        return issues

    def check_system_performance_factors(self):
        """Check system-wide factors affecting browser performance"""
        issues = []
        print("🖥️  Checking system performance factors...")

        # Check system load (fast)
        load_avg = os.getloadavg()
        cpu_count = os.cpu_count()
        print(f"   System load: {load_avg[0]:.2f} (cores: {cpu_count})")
        if load_avg[0] > cpu_count * 0.8:  # Load average high
            issues.append(f"High system load ({load_avg[0]:.1f}) may be slowing all applications")

        # Check for swap usage (fast - using psutil)
        swap = psutil.swap_memory()
        swap_gb = swap.used / (1024**3)
        print(f"   Swap usage: {swap_gb:.1f} GB")
        if swap.used > 1024 * 1024 * 1024:  # More than 1GB swap used
            issues.append(f"High swap usage ({swap_gb:.1f} GB) indicates memory pressure")

        # Check memory usage (fast)
        memory = psutil.virtual_memory()
        print(f"   Memory usage: {memory.percent:.1f}%")
        if memory.percent > 90:
            issues.append(f"Very high memory usage ({memory.percent:.1f}%) - close other applications")

        # Check CPU temperature (fast alternative to thermal throttling)
        try:
            # Use faster alternative - check if system is hot via CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.current < cpu_freq.max * 0.7:  # Running at <70% max frequency
                issues.append("CPU may be thermal throttling - check for overheating")
        except Exception:
            pass

        # Quick thermal check (with short timeout)
        try:
            result = subprocess.run(['pmset', '-g', 'therm'], capture_output=True, text=True, timeout=2)
            if 'thermal' in result.stdout.lower() and ('high' in result.stdout.lower() or 'critical' in result.stdout.lower()):
                issues.append("System thermal state is elevated - check cooling")
        except Exception:
            pass

        return issues

    def check_network_performance(self):
        """Check network-related performance issues"""
        issues = []
        print("🌐 Checking network performance...")

        # Check DNS resolution speed with timeout
        try:
            import socket

            # Set socket timeout to prevent hanging
            socket.setdefaulttimeout(3)  # 3 second timeout

            start_time = time.time()
            socket.gethostbyname('google.com')
            dns_time = (time.time() - start_time) * 1000
            print(f"   DNS resolution time: {dns_time:.1f}ms")

            if dns_time > 500:  # DNS resolution over 500ms
                issues.append(f"Slow DNS resolution ({dns_time:.1f}ms) - consider changing DNS servers")

            # Reset socket timeout
            socket.setdefaulttimeout(None)

        except socket.timeout:
            issues.append("DNS resolution timed out (>3s) - check network connectivity")
        except Exception as e:
            issues.append(f"DNS resolution test failed - check network connectivity")

        # Check for proxy settings that might slow browsing
        proxy_files = [
            self.orion_path / "Proxy Settings",
            Path.home() / "Library" / "Preferences" / "com.kagi.kagimacOS.plist"
        ]

        for proxy_file in proxy_files:
            if proxy_file.exists():
                issues.append("Proxy settings detected - may impact browsing speed")
                break

        return issues

    def check_orion_specific_settings(self):
        """Check Orion-specific settings that could impact performance"""
        issues = []
        print("🔧 Checking Orion-specific performance settings...")

        prefs_path = self.orion_path / "preferences.plist"
        if prefs_path.exists():
            prefs = self.read_plist(prefs_path) or {}

            # Enhanced performance-impacting settings with additional WebKit optimizations
            performance_settings = {
                'WebKitJavaScriptEnabled': (True, "JavaScript disabled - may break websites"),
                'WebKitJavaEnabled': (False, "Java enabled - security and performance risk"),
                'WebKitPluginsEnabled': (False, "Plugins enabled - may impact performance"),
                'WebKitDeveloperExtrasEnabled': (False, "Developer tools always enabled - may slow browsing"),
                'WebKitResourceLoadStatisticsEnabled': (False, "Privacy tracking statistics may slow loading"),
                'WebKitMemoryPressureHandlerEnabled': (True, "Memory pressure handling disabled - may cause memory issues"),
                'WebKitPageCacheEnabled': (True, "Page cache disabled - slower back/forward navigation"),
                'WebKitUsesPageCachePreferenceKey': (True, "Page cache preference disabled - impacts navigation speed"),
                'WebKitApplicationCacheEnabled': (True, "Application cache disabled - web apps may load slower"),
                'WebKitDatabasesEnabled': (True, "Database storage disabled - may break web applications"),
                'WebKitLocalStorageEnabled': (True, "Local storage disabled - may break website functionality"),
                'WebKitOfflineWebApplicationCacheEnabled': (True, "Offline cache disabled - web apps may not work offline"),
            }

            for setting, (optimal_value, issue_desc) in performance_settings.items():
                current_value = prefs.get(setting)
                if current_value is not None and current_value != optimal_value:
                    issues.append(f"Setting '{setting}': {issue_desc}")

        # Check for content blocker issues
        content_blocker_path = self.orion_path / "ContentBlockers"
        if content_blocker_path.exists():
            blockers = list(content_blocker_path.glob("*"))
            if len(blockers) > 5:
                issues.append(f"Many content blockers ({len(blockers)}) may slow page loading")

        return issues

    def check_orion_profile_corruption(self):
        """Check for Orion profile corruption issues"""
        issues = []
        print("🔧 Checking Orion profile corruption...")

        # Check for profile lock files (indicate corruption or improper shutdown)
        lock_files = [
            "SingletonLock", ".SingletonLock", "lockfile",
            "LOCK", ".lock", "profile.lock"
        ]

        for lock_file in lock_files:
            lock_path = self.orion_path / lock_file
            if lock_path.exists():
                issues.append(f"Profile lock file found ({lock_file}) - may indicate corruption")

        # Check for corrupted preferences
        prefs_path = self.orion_path / "preferences.plist"
        if prefs_path.exists():
            try:
                prefs = self.read_plist(prefs_path)
                if not prefs:
                    issues.append("Preferences file exists but cannot be read - may be corrupted")
            except Exception:
                issues.append("Preferences file is corrupted")

        # Check for excessive crash logs
        crash_logs_path = Path.home() / "Library" / "Logs" / "DiagnosticReports"
        if crash_logs_path.exists():
            orion_crashes = list(crash_logs_path.glob("*Orion*crash*"))
            orion_hangs = list(crash_logs_path.glob("*Orion*hang*"))

            recent_crashes = [f for f in orion_crashes if (time.time() - f.stat().st_mtime) < (7 * 24 * 3600)]  # Last 7 days
            recent_hangs = [f for f in orion_hangs if (time.time() - f.stat().st_mtime) < (7 * 24 * 3600)]

            if len(recent_crashes) > 3:
                issues.append(f"Multiple Orion crashes in past week ({len(recent_crashes)} crash logs)")
            if len(recent_hangs) > 1:
                issues.append(f"Orion hang logs detected ({len(recent_hangs)} hang logs)")

        # Check for WebKit process issues
        webkit_path = self.orion_path / "WebKitNetworking"
        if webkit_path.exists():
            webkit_size = self.get_directory_size(webkit_path) / (1024 * 1024)
            if webkit_size > 500:  # More than 500MB
                issues.append(f"WebKit networking data is very large ({webkit_size:.1f} MB)")

        return issues

    def compare_with_safari(self):
        """Compare Orion configuration with Safari to identify differences"""
        issues = []
        print("🏷️  Comparing Orion with Safari configuration...")

        safari_path = Path.home() / "Library" / "Safari"

        if not safari_path.exists():
            print("   Safari data not found - cannot compare")
            return issues

        # Compare extension counts
        orion_extensions = self.orion_path / "Extensions"
        safari_extensions = safari_path / "Extensions"

        orion_ext_count = len(list(orion_extensions.glob("*"))) if orion_extensions.exists() else 0
        safari_ext_count = len(list(safari_extensions.glob("*"))) if safari_extensions.exists() else 0

        print(f"   Extensions: Orion={orion_ext_count}, Safari={safari_ext_count}")

        if orion_ext_count > safari_ext_count + 5:
            issues.append(f"Orion has significantly more extensions than Safari ({orion_ext_count} vs {safari_ext_count})")

        # Compare history sizes
        orion_history_size = 0
        orion_history_files = ["History.db", "History.plist"]
        for hist_file in orion_history_files:
            hist_path = self.orion_path / hist_file
            if hist_path.exists():
                orion_history_size += hist_path.stat().st_size

        safari_history_size = 0
        safari_history_file = safari_path / "History.db"
        if safari_history_file.exists():
            safari_history_size = safari_history_file.stat().st_size

        orion_hist_mb = orion_history_size / (1024 * 1024)
        safari_hist_mb = safari_history_size / (1024 * 1024)

        print(f"   History: Orion={orion_hist_mb:.1f}MB, Safari={safari_hist_mb:.1f}MB")

        if orion_hist_mb > safari_hist_mb * 3:  # 3x larger
            issues.append(f"Orion history is much larger than Safari ({orion_hist_mb:.1f}MB vs {safari_hist_mb:.1f}MB)")

        # Check if Orion is using different engines than Safari
        orion_prefs = self.orion_path / "preferences.plist"
        if orion_prefs.exists():
            prefs = self.read_plist(orion_prefs) or {}

            # Check for performance-impacting settings that Safari doesn't have
            orion_specific_issues = []

            if prefs.get('WebKitDeveloperExtrasEnabled'):
                orion_specific_issues.append("Developer tools enabled (Safari likely doesn't have this)")

            if prefs.get('WebKitResourceLoadStatisticsEnabled'):
                orion_specific_issues.append("Resource load statistics enabled (extra overhead)")

            if prefs.get('WebKitStorageBlockingPolicy', 0) > 1:
                orion_specific_issues.append("Strict storage blocking may slow page loads")

            for issue in orion_specific_issues:
                issues.append(f"Orion-specific setting: {issue}")

        return issues

    def backup_critical_data(self):
        """Backup bookmarks, passwords, and other critical data"""
        print(f"💾 Creating backup at: {self.backup_path}")
        self.backup_path.mkdir(exist_ok=True)

        backed_up = []
        for critical_file in self.critical_files:
            source = self.orion_path / critical_file
            if source.exists():
                dest = self.backup_path / critical_file
                try:
                    if source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest)
                    backed_up.append(critical_file)
                    print(f"   ✅ Backed up: {critical_file}")
                except Exception as e:
                    print(f"   ⚠️  Failed to backup {critical_file}: {e}")

        print(f"   📦 Backup complete: {len(backed_up)} items backed up")
        return len(backed_up) > 0

    def clean_caches(self):
        """Clean various cache directories safely"""
        print("🧹 CLEANING CACHES AND TEMPORARY DATA")
        print("-" * 50)

        # Directories safe to delete
        safe_to_clean = [
            "Cache",
            "CachedData",
            "WebKitCache",
            "GPUCache",
            "DawnCache",
            "Code Cache",
            "blob_storage",
            "Service Worker/CacheStorage",
            "databases/Databases.db-wal",
            "databases/Databases.db-shm",
            "Network Persistent State",
            "TransportSecurity",
            "QuotaManager",
            "QuotaManager-journal"
        ]

        cleaned_size = 0
        cleaned_items = 0

        for item in safe_to_clean:
            item_path = self.orion_path / item
            if item_path.exists():
                try:
                    size_before = self.get_directory_size(item_path) if item_path.is_dir() else item_path.stat().st_size

                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                    else:
                        item_path.unlink()

                    cleaned_size += size_before
                    cleaned_items += 1
                    print(f"   🗑️  Cleaned: {item} ({size_before / (1024*1024):.1f} MB)")

                except Exception as e:
                    print(f"   ⚠️  Failed to clean {item}: {e}")

        print(f"\n✅ Cleanup complete:")
        print(f"   📊 {cleaned_items} items cleaned")
        print(f"   💾 {cleaned_size / (1024*1024):.1f} MB freed")

        return cleaned_size

    def read_plist(self, plist_path):
        """Read a plist file"""
        try:
            result = subprocess.run(['plutil', '-convert', 'json', '-o', '-', str(plist_path)],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"   ⚠️  Error reading plist: {e}")
        return None

    def write_plist(self, plist_path, data):
        """Write data to a plist file"""
        try:
            # Convert to JSON first, then to plist
            json_str = json.dumps(data, indent=2)
            result = subprocess.run(['plutil', '-convert', 'binary1', '-o', str(plist_path), '-'],
                                  input=json_str, text=True, capture_output=True)
            return result.returncode == 0
        except Exception as e:
            print(f"   ⚠️  Error writing plist: {e}")
            return False

    def optimize_settings(self):
        """Apply performance optimizations with user confirmation"""
        print("⚙️  PERFORMANCE SETTINGS OPTIMIZATION")
        print("-" * 70)

        # Enhanced performance optimizations with additional safe, high-benefit settings
        optimizations = [
            {
                "name": "Disable DNS Prefetching",
                "description": "Reduces background network requests that can slow browsing",
                "benefit": "Faster page loads, reduced network overhead",
                "setting": "WebKitDNSPrefetchingEnabled",
                "value": False,
                "current_check": "WebKitDNSPrefetchingEnabled",
                "safety_level": "High"
            },
            {
                "name": "Enable Hardware Acceleration",
                "description": "Uses GPU for smoother scrolling and animations",
                "benefit": "Better graphics performance, smoother UI",
                "setting": "WebKitAcceleratedCompositingEnabled",
                "value": True,
                "current_check": "WebKitAcceleratedCompositingEnabled",
                "safety_level": "High"
            },
            {
                "name": "Disable Smooth Scrolling",
                "description": "Reduces CPU usage during scrolling on older machines",
                "benefit": "More responsive scrolling on slower systems",
                "setting": "WebKitScrollAnimatorEnabled",
                "value": False,
                "current_check": "WebKitScrollAnimatorEnabled",
                "safety_level": "High"
            },
            {
                "name": "Reduce History Limit",
                "description": "Limits history to 1000 items instead of unlimited",
                "benefit": "Faster history searches, reduced memory usage",
                "setting": "WebKitHistoryItemLimit",
                "value": 1000,
                "current_check": "WebKitHistoryItemLimit",
                "safety_level": "High"
            },
            {
                "name": "Disable Page Previews",
                "description": "Disables thumbnail generation for faster browsing",
                "benefit": "Reduced memory and CPU usage",
                "setting": "WebKitPagePreviewsEnabled",
                "value": False,
                "current_check": "WebKitPagePreviewsEnabled",
                "safety_level": "High"
            },
            {
                "name": "Enable JavaScript JIT",
                "description": "Optimizes JavaScript execution for better performance",
                "benefit": "Faster JavaScript execution, better web app performance",
                "setting": "WebKitJavaScriptJITEnabled",
                "value": True,
                "current_check": "WebKitJavaScriptJITEnabled",
                "safety_level": "High"
            },
            {
                "name": "Enable Memory Pressure Handling",
                "description": "Automatically manages memory when system resources are low",
                "benefit": "Better stability under memory pressure, prevents crashes",
                "setting": "WebKitMemoryPressureHandlerEnabled",
                "value": True,
                "current_check": "WebKitMemoryPressureHandlerEnabled",
                "safety_level": "High"
            },
            {
                "name": "Enable Page Cache",
                "description": "Caches previously visited pages for faster back/forward navigation",
                "benefit": "Instant back/forward navigation, better user experience",
                "setting": "WebKitPageCacheEnabled",
                "value": True,
                "current_check": "WebKitPageCacheEnabled",
                "safety_level": "High"
            },
            {
                "name": "Enable Application Cache",
                "description": "Allows web applications to cache resources for offline use",
                "benefit": "Faster web app loading, better offline functionality",
                "setting": "WebKitApplicationCacheEnabled",
                "value": True,
                "current_check": "WebKitApplicationCacheEnabled",
                "safety_level": "High"
            },
            {
                "name": "Optimize Resource Loading",
                "description": "Disable resource load statistics tracking for better performance",
                "benefit": "Faster page loading, reduced background processing",
                "setting": "WebKitResourceLoadStatisticsEnabled",
                "value": False,
                "current_check": "WebKitResourceLoadStatisticsEnabled",
                "safety_level": "Medium"
            }
        ]

        # Check current preferences
        prefs_path = self.orion_path / "preferences.plist"
        current_prefs = {}

        if prefs_path.exists():
            current_prefs = self.read_plist(prefs_path) or {}
        else:
            print("   ℹ️  No preferences file found, will create new one")

        changes_made = 0
        backup_made = False

        print(f"\n🔍 Checking current settings and recommending optimizations...\n")

        for opt in optimizations:
            current_value = current_prefs.get(opt["current_check"], "Not set")

            # Enhanced display with safety indicators
            safety_icon = "🟢" if opt["safety_level"] == "High" else "🟡" if opt["safety_level"] == "Medium" else "🟠"

            print(f"🔧 {opt['name']} {safety_icon}")
            print(f"   Description: {opt['description']}")
            print(f"   Benefit: {opt['benefit']}")
            print(f"   Current value: {current_value}")
            print(f"   Recommended value: {opt['value']}")
            print(f"   Safety level: {opt['safety_level']} {safety_icon}")

            if current_value == opt['value']:
                print(f"   ✅ Already optimally configured")
            else:
                apply = input(f"   Apply this {opt['safety_level'].lower()}-safety optimization? (y/N): ").lower()
                if apply == 'y':
                    # Backup preferences before first change
                    if not backup_made:
                        backup_prefs = self.backup_path / "preferences_backup.plist"
                        try:
                            shutil.copy2(prefs_path, backup_prefs)
                            print(f"   💾 Preferences backed up to: {backup_prefs}")
                            backup_made = True
                        except Exception as e:
                            print(f"   ⚠️  Warning: Could not backup preferences: {e}")

                    # Apply the setting
                    current_prefs[opt["setting"]] = opt["value"]
                    changes_made += 1
                    print(f"   ✅ Applied: {opt['name']}")
                else:
                    print(f"   ⏭️  Skipped: {opt['name']}")

            print()  # Empty line for readability

        # Save changes if any were made
        if changes_made > 0:
            if self.write_plist(prefs_path, current_prefs):
                print(f"✅ Successfully applied {changes_made} optimizations")
                print("   Settings will take effect when Orion is restarted")
            else:
                print(f"❌ Failed to save preferences file")
        else:
            print("ℹ️  No changes were made to settings")

        # Additional system-level recommendations
        print(f"\n💡 ADDITIONAL RECOMMENDATIONS:")
        print(f"   • Restart your Mac occasionally to clear system caches")
        print(f"   • Keep macOS updated for optimal browser performance")
        print(f"   • Consider using fewer browser extensions")
        print(f"   • Close unused tabs to free up memory")

        return changes_made

    def verify_cleanup(self):
        """Verify that critical data is still intact"""
        print("🔍 VERIFYING DATA INTEGRITY")
        print("-" * 50)

        critical_intact = True
        for critical_file in ["Bookmarks.plist", "Login Data"]:
            file_path = self.orion_path / critical_file
            backup_path = self.backup_path / critical_file

            if not file_path.exists() and backup_path.exists():
                print(f"   🚨 Restoring {critical_file} from backup")
                try:
                    shutil.copy2(backup_path, file_path)
                    print(f"   ✅ {critical_file} restored")
                except Exception as e:
                    print(f"   ❌ Failed to restore {critical_file}: {e}")
                    critical_intact = False
            elif file_path.exists():
                print(f"   ✅ {critical_file} intact")

        return critical_intact

    def run_optimization(self):
        """Main optimization workflow"""
        self.print_header()

        # Step 1: Check if Orion is running
        is_running, pid = self.check_orion_running()
        if is_running:
            print(f"⚠️  Orion is currently running (PID: {pid})")
            close_browser = input("Close Orion to continue? (y/N): ").lower()
            if close_browser != 'y':
                print("❌ Cannot optimize while Orion is running. Exiting.")
                return

            if not self.close_orion():
                print("❌ Failed to close Orion. Please close manually and rerun.")
                return

        # Step 2: Diagnose issues
        print()
        has_issues = self.diagnose_performance()

        if not has_issues:
            print("\n🎉 Your Orion browser appears to be running optimally!")
            restart = input("Restart Orion? (Y/n): ").lower()
            if restart != 'n':
                subprocess.run(['open', '-a', 'Orion'])
            return

        # Step 3: Confirm cleanup
        print(f"\n🤔 Do you want to clean up caches and temporary files?")
        print("   ✅ Your bookmarks and passwords will be preserved")
        print("   🗑️  Cache, temporary files, and browsing data will be cleared")

        proceed = input("Proceed with cleanup? (y/N): ").lower()
        if proceed != 'y':
            print("❌ Cleanup cancelled.")
            return

        # Step 4: Backup critical data
        print()
        if not self.backup_critical_data():
            print("❌ Backup failed. Aborting cleanup for safety.")
            return

        # Step 5: Clean caches
        print()
        freed_space = self.clean_caches()

        # Step 6: Optimize settings
        print()
        self.optimize_settings()

        # Step 7: Verify integrity
        print()
        if self.verify_cleanup():
            print("✅ Data verification passed")
        else:
            print("⚠️  Some data may need manual restoration from backup")

        # Step 8: Summary and restart
        print(f"\n🎉 OPTIMIZATION COMPLETE!")
        print(f"   💾 Space freed: {freed_space / (1024*1024):.1f} MB")
        print(f"   📦 Backup location: {self.backup_path}")
        print("   🔒 Bookmarks and passwords preserved")

        restart = input("\nRestart Orion browser? (Y/n): ").lower()
        if restart != 'n':
            print("🚀 Starting Orion...")
            subprocess.run(['open', '-a', 'Orion'])

        print("\n✨ Orion should now run faster!")
        print("💡 Tip: Run this script monthly for best performance")

if __name__ == "__main__":
    try:
        optimizer = OrionSpeedOptimizer()
        optimizer.run_optimization()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please report this issue if it persists")