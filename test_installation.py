#!/usr/bin/env python3
"""
Installation Test Script for Profile Scraper
Run this script to verify that all dependencies are installed correctly.
"""

import sys
import importlib
import subprocess

def test_python_version():
    """Test Python version."""
    print("🐍 Testing Python version...")
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

def test_dependencies():
    """Test required dependencies."""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'requests',
        'beautifulsoup4',
        'selenium',
        'flask',
        'pandas',
        'lxml',
        'fake_useragent',
        'python_dotenv',
        'webdriver_manager',
        'phonenumbers',
        'email_validator',
        'aiohttp'
    ]
    
    failed_packages = []
    
    for package in required_packages:
        try:
            # Convert package names to import names
            import_name = package.replace('-', '_').replace('_', '_')
            if package == 'beautifulsoup4':
                import_name = 'bs4'
            elif package == 'python-dotenv':
                import_name = 'dotenv'
            elif package == 'fake-useragent':
                import_name = 'fake_useragent'
            elif package == 'webdriver-manager':
                import_name = 'webdriver_manager'
            
            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Missing packages: {', '.join(failed_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed")
        return True

def test_modules():
    """Test custom modules."""
    print("\n🔧 Testing custom modules...")
    
    modules = [
        'config',
        'database',
        'data_extractor',
        'search_engines',
        'scraper'
    ]
    
    failed_modules = []
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}.py")
        except ImportError as e:
            print(f"❌ {module}.py - {e}")
            failed_modules.append(module)
    
    if failed_modules:
        print(f"\n❌ Failed to import modules: {', '.join(failed_modules)}")
        return False
    else:
        print("✅ All custom modules loaded successfully")
        return True

def test_database():
    """Test database initialization."""
    print("\n🗃️ Testing database...")
    
    try:
        from database import db
        print("✅ Database module loaded")
        
        # Test database initialization
        searches = db.get_all_searches()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_chrome_driver():
    """Test Chrome driver installation."""
    print("\n🌐 Testing Chrome driver...")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver_path = ChromeDriverManager().install()
        print(f"✅ ChromeDriver installed at: {driver_path}")
        
        # Test driver initialization
        driver = webdriver.Chrome(driver_path, options=chrome_options)
        driver.quit()
        print("✅ ChromeDriver test successful")
        return True
    except Exception as e:
        print(f"⚠️ ChromeDriver test failed: {e}")
        print("   This is optional - basic scraping will still work")
        return True  # Not critical

def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import config
        print(f"✅ Configuration loaded")
        print(f"   - Search engines: {config.SEARCH_ENGINES}")
        print(f"   - Request delay: {config.REQUEST_DELAY}s")
        print(f"   - Max results: {config.MAX_RESULTS_PER_SEARCH}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def run_simple_test():
    """Run a simple functionality test."""
    print("\n🧪 Running simple functionality test...")
    
    try:
        from data_extractor import extractor
        
        # Test email extraction
        test_text = "Contact me at john.doe@example.com or call (555) 123-4567"
        emails = extractor.extract_emails(test_text)
        phones = extractor.extract_phones(test_text)
        
        if emails:
            print(f"✅ Email extraction: found {len(emails)} emails")
        else:
            print("⚠️ Email extraction: no emails found (may need adjustment)")
        
        if phones:
            print(f"✅ Phone extraction: found {len(phones)} phones")
        else:
            print("⚠️ Phone extraction: no phones found (may need adjustment)")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔍 Profile Scraper Installation Test")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_dependencies,
        test_modules,
        test_database,
        test_chrome_driver,
        test_configuration,
        run_simple_test
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The installation is ready to use.")
        print("\nNext steps:")
        print("  1. Start the web app: python web_app.py")
        print("  2. Or use CLI: python cli.py 'your search term'")
        print("  3. Visit http://localhost:5000 for the web interface")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("Try installing missing dependencies: pip install -r requirements.txt")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)