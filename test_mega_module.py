#!/usr/bin/env python3
"""
Test Script for Recreated Mega Module

This script tests various aspects of the recreated mega module using the provided URL:
https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the pyobidl directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyobidl'))

from pyobidl.megacli.mega import Mega
from pyobidl.downloader import UniversalDownloader
from pyobidl.utils import setup_logging

# Test URL from the provided link
TEST_URL = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"
DOWNLOAD_DIR = "./test_downloads"

logger = logging.getLogger(__name__)


def test_url_parsing():
    """Test URL parsing functionality"""
    print("\n" + "="*60)
    print("🧪 Testing URL Parsing")
    print("="*60)
    
    mega = Mega()
    
    # Test the URL parsing
    file_id, decryption_key = mega.parse_mega_url(TEST_URL)
    
    if file_id and decryption_key:
        print(f"✅ URL parsing successful!")
        print(f"   File ID: {file_id}")
        print(f"   Decryption Key: {decryption_key[:20]}...")
        return True
    else:
        print(f"❌ URL parsing failed!")
        return False


def test_simple_download():
    """Test the simple download method (tries megatools first)"""
    print("\n" + "="*60)
    print("🧪 Testing Simple Download Method")
    print("="*60)
    
    try:
        mega = Mega()
        
        # Create download directory
        Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
        
        print(f"📥 Attempting download using simple_download method...")
        print(f"📁 Download directory: {DOWNLOAD_DIR}")
        
        start_time = time.time()
        success = mega.simple_download(TEST_URL, DOWNLOAD_DIR)
        end_time = time.time()
        
        if success:
            print(f"✅ Simple download completed successfully!")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            
            # List downloaded files
            downloaded_files = list(Path(DOWNLOAD_DIR).glob("*"))
            if downloaded_files:
                print(f"📄 Downloaded files:")
                for file in downloaded_files:
                    file_size = file.stat().st_size
                    print(f"   - {file.name} ({file_size:,} bytes)")
            
            return True
        else:
            print(f"❌ Simple download failed!")
            return False
            
    except Exception as e:
        print(f"❌ Simple download error: {e}")
        return False


def test_universal_downloader():
    """Test the universal downloader"""
    print("\n" + "="*60)
    print("🧪 Testing Universal Downloader")
    print("="*60)
    
    try:
        downloader = UniversalDownloader()
        
        # Test platform detection
        platform = downloader.detect_platform(TEST_URL)
        print(f"🔍 Detected platform: {platform}")
        
        if platform != 'mega':
            print(f"❌ Platform detection failed! Expected 'mega', got '{platform}'")
            return False
        
        print(f"✅ Platform detection successful!")
        
        # Test download
        universal_dir = os.path.join(DOWNLOAD_DIR, "universal")
        Path(universal_dir).mkdir(exist_ok=True)
        
        print(f"📥 Attempting download using UniversalDownloader...")
        start_time = time.time()
        success = downloader.download(TEST_URL, universal_dir)
        end_time = time.time()
        
        if success:
            print(f"✅ Universal downloader completed successfully!")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            return True
        else:
            print(f"❌ Universal downloader failed!")
            return False
            
    except Exception as e:
        print(f"❌ Universal downloader error: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid URLs"""
    print("\n" + "="*60)
    print("🧪 Testing Error Handling")
    print("="*60)
    
    mega = Mega()
    
    # Test invalid URLs
    invalid_urls = [
        "https://mega.nz/file/invalid",
        "https://mega.nz/file/5r1nWZwK",  # Missing decryption key
        "https://example.com/not-mega",
        "invalid-url"
    ]
    
    errors_handled_correctly = 0
    
    for url in invalid_urls:
        print(f"🔍 Testing invalid URL: {url}")
        file_id, key = mega.parse_mega_url(url)
        
        if file_id is None and key is None:
            print(f"✅ Correctly identified invalid URL")
            errors_handled_correctly += 1
        else:
            print(f"❌ Failed to identify invalid URL")
    
    if errors_handled_correctly == len(invalid_urls):
        print(f"✅ Error handling test passed ({errors_handled_correctly}/{len(invalid_urls)})")
        return True
    else:
        print(f"❌ Error handling test failed ({errors_handled_correctly}/{len(invalid_urls)})")
        return False


def test_cli_interfaces():
    """Test CLI interfaces"""
    print("\n" + "="*60)
    print("🧪 Testing CLI Interfaces")
    print("="*60)
    
    try:
        # Just check if the CLI script exists and is importable
        cli_script = "mega_downloader_cli.py"
        if os.path.exists(cli_script):
            print(f"✅ CLI script found: {cli_script}")
        else:
            print(f"❌ CLI script not found: {cli_script}")
            return False
        
        # Test if quick_test.py exists
        quick_script = "quick_test.py"
        if os.path.exists(quick_script):
            print(f"✅ Quick test script found: {quick_script}")
        else:
            print(f"❌ Quick test script not found: {quick_script}")
            return False
        
        # Test if demo_cli_usage.py exists
        demo_script = "demo_cli_usage.py"
        if os.path.exists(demo_script):
            print(f"✅ Demo CLI script found: {demo_script}")
        else:
            print(f"❌ Demo CLI script not found: {demo_script}")
            return False
        
        print(f"✅ All CLI interfaces are available!")
        return True
        
    except Exception as e:
        print(f"❌ CLI interface test error: {e}")
        return False


def cleanup_test_files():
    """Clean up test download files"""
    try:
        import shutil
        if os.path.exists(DOWNLOAD_DIR):
            shutil.rmtree(DOWNLOAD_DIR)
            print(f"🧹 Cleaned up test directory: {DOWNLOAD_DIR}")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


def main():
    """Run all tests"""
    print("🚀 Mega Module Test Suite")
    print("="*60)
    print(f"🔗 Test URL: {TEST_URL}")
    print(f"📁 Download Directory: {DOWNLOAD_DIR}")
    
    # Setup logging
    setup_logging(verbose=True)
    
    # Test results
    results = {
        "URL Parsing": False,
        "Simple Download": False,
        "Universal Downloader": False,
        "Error Handling": False,
        "CLI Interfaces": False
    }
    
    # Run tests
    try:
        results["URL Parsing"] = test_url_parsing()
        results["Error Handling"] = test_error_handling()
        results["CLI Interfaces"] = test_cli_interfaces()
        
        # Only run download tests if URL parsing works
        if results["URL Parsing"]:
            results["Simple Download"] = test_simple_download()
            results["Universal Downloader"] = test_universal_downloader()
        else:
            print("\n⚠️  Skipping download tests due to URL parsing failure")
    
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during tests: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The mega module is working correctly.")
    elif passed > 0:
        print("⚠️  Some tests passed. Check individual results above.")
    else:
        print("❌ All tests failed. Please check the module installation and dependencies.")
    
    # Ask about cleanup
    print("\n" + "="*60)
    try:
        cleanup_choice = input("🧹 Clean up downloaded test files? (y/N): ").lower().strip()
        if cleanup_choice in ['y', 'yes']:
            cleanup_test_files()
        else:
            print(f"📁 Test files preserved in: {DOWNLOAD_DIR}")
    except (KeyboardInterrupt, EOFError):
        print(f"\n📁 Test files preserved in: {DOWNLOAD_DIR}")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 