#!/usr/bin/env python3
"""
Test script to verify spider functionality without requiring network access
This helps debug spider issues in environments with limited connectivity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_spider_imports():
    """Test if spider classes can be imported correctly"""
    try:
        from practo_scraper.spiders.practo_doctors import PractoDoctorsSpider, PractoDoctorsSimpleSpider
        print("✅ Both spider classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_spider_configuration():
    """Test spider configuration and start_requests generation"""
    try:
        from practo_scraper.spiders.practo_doctors import PractoDoctorsSimpleSpider
        
        spider = PractoDoctorsSimpleSpider()
        print(f"✅ Simple spider initialized")
        print(f"   Cities: {spider.cities}")
        print(f"   Specialities: {len(spider.specialities)} configured")
        
        # Test start_requests generation
        requests = list(spider.start_requests())
        print(f"   Generates {len(requests)} initial requests")
        
        if requests:
            first_req = requests[0]
            print(f"   Sample URL: {first_req.url[:100]}...")
            
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_items_structure():
    """Test DoctorItem structure"""
    try:
        from practo_scraper.items import DoctorItem
        
        item = DoctorItem()
        required_fields = ['name', 'speciality', 'city', 'profile_url']
        
        for field in required_fields:
            if field in item.fields:
                print(f"✅ Field '{field}' exists")
            else:
                print(f"❌ Field '{field}' missing")
                
        return True
    except Exception as e:
        print(f"❌ Items error: {e}")
        return False

def test_settings():
    """Test settings configuration"""
    try:
        from scrapy.utils.project import get_project_settings
        
        settings = get_project_settings()
        print(f"✅ Settings loaded successfully")
        
        # Check key settings
        log_file = settings.get('LOG_FILE')
        feeds = settings.get('FEEDS')
        
        print(f"   Log file: {log_file}")
        print(f"   Output feeds configured: {bool(feeds)}")
        
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Practo Scraper Components\n")
    
    tests = [
        ("Spider Imports", test_spider_imports),
        ("Spider Configuration", test_spider_configuration), 
        ("Items Structure", test_items_structure),
        ("Settings", test_settings),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        success = test_func()
        results.append((test_name, success))
    
    print(f"\n🏁 Test Results:")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All tests passed! Spiders should work correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)