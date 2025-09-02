#!/usr/bin/env python3
"""
Diagnostic script for Practo scraper issues
This helps identify and fix common scraping problems
"""

import sys
import os
import subprocess
from pathlib import Path

def check_network_connectivity():
    """Check if we can reach Practo website"""
    print("🌐 Checking network connectivity...")
    
    try:
        import requests
        response = requests.get("https://www.practo.com", timeout=10)
        if response.status_code == 200:
            print("✅ Can reach Practo website")
            return True
        else:
            print(f"⚠️  Practo returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach Practo website: {e}")
        print("   This might be due to:")
        print("   - No internet connection")
        print("   - Firewall blocking the request")
        print("   - Practo blocking automated requests")
        return False

def check_playwright_installation():
    """Check if Playwright is properly installed"""
    print("\n🎭 Checking Playwright installation...")
    
    try:
        import playwright
        print("✅ Playwright package installed")
        
        # Check if browsers are installed
        try:
            result = subprocess.run([sys.executable, "-m", "playwright", "--help"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Playwright CLI available")
                
                # Try to check browser installation
                result = subprocess.run([sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"], 
                                      capture_output=True, text=True, timeout=30)
                if "chromium" in result.stdout.lower():
                    print("✅ Chromium browser configuration available")
                else:
                    print("⚠️  Chromium browser might not be installed")
                    print("   Run: python -m playwright install chromium")
                
                return True
            else:
                print(f"❌ Playwright CLI error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Playwright command timed out")
            return False
            
    except ImportError:
        print("❌ Playwright package not installed")
        print("   Install with: pip install playwright")
        return False

def check_log_files():
    """Check existing log files for clues"""
    print("\n📋 Checking log files...")
    
    log_files = ["scrapy.log", "spider.log", "error.log"]
    found_logs = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            found_logs.append(log_file)
            file_size = os.path.getsize(log_file)
            print(f"📄 Found {log_file} ({file_size} bytes)")
            
            # Show last few lines
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"   Last entries:")
                        for line in lines[-3:]:
                            print(f"   {line.strip()}")
            except Exception as e:
                print(f"   Error reading file: {e}")
    
    if not found_logs:
        print("📄 No log files found - this might be the first run")
    
    return found_logs

def check_data_files():
    """Check existing data files"""
    print("\n💾 Checking data files...")
    
    data_dir = Path("data")
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        db_files = list(data_dir.glob("*.db"))
        
        print(f"📊 Found {len(csv_files)} CSV files and {len(db_files)} database files")
        
        for csv_file in csv_files[:3]:  # Show first 3
            file_size = csv_file.stat().st_size
            print(f"   {csv_file.name} ({file_size} bytes)")
            
        if csv_files:
            print("✅ Previous scraping data exists - scraper was working before")
            return True
    else:
        print("📊 No data directory found")
    
    return False

def suggest_fixes():
    """Suggest potential fixes based on findings"""
    print("\n🔧 Suggested fixes:")
    
    print("1. 🕷️  For missing simple spider:")
    print("   - The simple spider has been added")
    print("   - Use: python run_scraper.py --spider simple")
    
    print("\n2. 🎭 For Playwright issues:")
    print("   - Install browsers: python -m playwright install chromium")
    print("   - Or use simple spider as fallback")
    
    print("\n3. 🌐 For network issues:")
    print("   - Check internet connection")
    print("   - Try VPN if blocked")
    print("   - Use existing data for testing")
    
    print("\n4. 📊 For data issues:")
    print("   - Check data/ directory for previous results")
    print("   - Verify CSV files are not corrupted")
    
    print("\n5. ⚙️  General troubleshooting:")
    print("   - Check scrapy.log for detailed errors")
    print("   - Run with debug: scrapy crawl practo_doctors_simple -L DEBUG")
    print("   - Test individual components with test_spiders.py")

def main():
    """Run comprehensive diagnostics"""
    print("🔍 Practo Scraper Diagnostics\n")
    
    # Change to scraper directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    network_ok = check_network_connectivity()
    playwright_ok = check_playwright_installation() 
    logs_found = check_log_files()
    data_exists = check_data_files()
    
    suggest_fixes()
    
    print(f"\n📋 Summary:")
    print(f"   Network Access: {'✅' if network_ok else '❌'}")
    print(f"   Playwright Ready: {'✅' if playwright_ok else '❌'}")
    print(f"   Previous Data: {'✅' if data_exists else '❌'}")
    print(f"   Log Files: {'✅' if logs_found else '📄'}")
    
    if not network_ok:
        print(f"\n⚠️  Main issue appears to be network connectivity.")
        print(f"   The simple spider should work when network access is restored.")
    elif not playwright_ok:
        print(f"\n⚠️  Main issue appears to be Playwright setup.")
        print(f"   Use the simple spider or fix Playwright installation.")
    else:
        print(f"\n✅ System appears ready for scraping!")

if __name__ == "__main__":
    main()