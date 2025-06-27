#!/usr/bin/env python3
"""
Test Script: Adapting Old Downloader Usage to New Recreated Mega Module

This shows how to replace the old Downloader class with the new system.
"""

import os
import sys
from pathlib import Path

# Add the pyobidl directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyobidl'))

from pyobidl.megacli.mega import Mega
from pyobidl.downloader import UniversalDownloader
from pyobidl.utils import setup_logging

# Test URL
TEST_URL = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"

def test_old_style_usage():
    """Test using the old style approach"""
    print("🔄 Testing Old Style Usage Adaptation")
    print("="*50)
    
    # OLD WAY (what you were trying to do):
    # extract_folder = "temp"
    # dl = Downloader(destpath=extract_folder)
    
    # NEW WAY - Option 1: Universal Downloader (Recommended)
    extract_folder = "temp"
    Path(extract_folder).mkdir(exist_ok=True)
    
    print(f"📁 Using destination: {extract_folder}")
    
    # Create universal downloader (handles all platforms)
    dl = UniversalDownloader()
    
    print("✅ UniversalDownloader created successfully!")
    
    return dl, extract_folder

def test_download_methods(dl, extract_folder):
    """Test different download methods"""
    print("\n🧪 Testing Download Methods")
    print("="*50)
    
    # Method 1: Universal Downloader (auto-detects platform)
    print("📥 Method 1: Universal Download")
    try:
        success = dl.download(TEST_URL, extract_folder)
        if success:
            print("✅ Universal download successful!")
        else:
            print("❌ Universal download failed!")
    except Exception as e:
        print(f"❌ Universal download error: {e}")
    
    # Method 2: Direct Mega Download (like your original script)
    print("\n📥 Method 2: Direct Mega Download")
    try:
        mega = Mega()
        success = mega.simple_download(TEST_URL, extract_folder)
        if success:
            print("✅ Direct mega download successful!")
        else:
            print("❌ Direct mega download failed!")
    except Exception as e:
        print(f"❌ Direct mega download error: {e}")

def test_old_methods_equivalent():
    """Show how old Downloader methods map to new system"""
    print("\n🔄 Old vs New Method Mapping")
    print("="*50)
    
    extract_folder = "temp"
    Path(extract_folder).mkdir(exist_ok=True)
    
    # OLD: dl.download_url(url)
    # NEW: Multiple options
    
    print("📋 Method Equivalents:")
    print("OLD: dl = Downloader(destpath='temp')")
    print("NEW: dl = UniversalDownloader()")
    print()
    print("OLD: dl.download_url(url)")
    print("NEW: dl.download(url, 'temp')")
    print()
    print("OLD: dl.download_info(url)")
    print("NEW: dl.detect_platform(url) + individual platform methods")
    
    # Demonstrate
    dl = UniversalDownloader()
    
    # Show platform detection
    platform = dl.detect_platform(TEST_URL)
    print(f"\n🔍 Platform detection: {platform}")
    
    # Show download info equivalent
    if platform == 'mega':
        mega = Mega()
        file_id, key = mega.parse_mega_url(TEST_URL)
        print(f"📋 File info: ID={file_id}, Key={key[:15]}...")

def test_progress_and_args():
    """Test progress callback equivalent"""
    print("\n📊 Progress Tracking")
    print("="*50)
    
    # In the old system, you could do:
    # dl.download_url(url, progressfunc=my_callback, args=my_args)
    
    # In the new system, progress is handled via logging
    setup_logging(verbose=True)
    
    print("💡 Progress tracking is now handled via logging system")
    print("   Use setup_logging(verbose=True) for detailed progress")

def show_file_results(extract_folder):
    """Show downloaded files"""
    print(f"\n📁 Files in {extract_folder}:")
    print("="*50)
    
    if os.path.exists(extract_folder):
        files = [f for f in os.listdir(extract_folder) if os.path.isfile(os.path.join(extract_folder, f))]
        if files:
            for file in files:
                file_path = os.path.join(extract_folder, file)
                size = os.path.getsize(file_path)
                print(f"📄 {file} ({size:,} bytes)")
        else:
            print("📂 (empty)")
    else:
        print("📂 (directory doesn't exist)")

def main():
    """Main test function"""
    print("🚀 Testing New Downloader System")
    print("="*60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Test old style adaptation
        dl, extract_folder = test_old_style_usage()
        
        # Show method mapping
        test_old_methods_equivalent()
        
        # Test progress
        test_progress_and_args()
        
        # Test actual downloads
        test_download_methods(dl, extract_folder)
        
        # Show results
        show_file_results(extract_folder)
        
        print(f"\n🎉 Testing completed!")
        print(f"💡 Your old code can be easily adapted:")
        print(f"   OLD: dl = Downloader(destpath='{extract_folder}')")
        print(f"   NEW: dl = UniversalDownloader()")
        print(f"   OLD: dl.download_url(url)")
        print(f"   NEW: dl.download(url, '{extract_folder}')")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 