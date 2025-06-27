#!/usr/bin/env python3
"""
Quick Test - Download the provided Mega.nz file

This script quickly tests the mega module by downloading:
https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI
"""

import os
import sys
import time
from pathlib import Path

# Add the pyobidl directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyobidl'))

from pyobidl.megacli.mega import Mega
from pyobidl.utils import setup_logging

# Test URL
TEST_URL = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"

def main():
    print("🚀 Quick Mega Download Test")
    print("="*50)
    print(f"URL: {TEST_URL}")
    
    # Setup basic logging
    setup_logging()
    
    try:
        # Create Mega instance
        print("\n📦 Creating Mega instance...")
        mega = Mega()
        
        # Parse URL
        print("🔍 Parsing URL...")
        file_id, key = mega.parse_mega_url(TEST_URL)
        
        if file_id and key:
            print(f"✅ URL parsed successfully!")
            print(f"   File ID: {file_id}")
            print(f"   Key: {key[:15]}...")
        else:
            print("❌ Failed to parse URL!")
            return False
        
        # Create download directory
        download_dir = "./quick_download"
        Path(download_dir).mkdir(exist_ok=True)
        print(f"📁 Download directory: {download_dir}")
        
        # Attempt download
        print("\n🚀 Starting download...")
        print("   (This will try megatools first, then show instructions if not available)")
        
        start_time = time.time()
        success = mega.simple_download(TEST_URL, download_dir)
        end_time = time.time()
        
        if success:
            print(f"\n✅ Download completed successfully!")
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            
            # Show downloaded files
            downloaded_files = list(Path(download_dir).glob("*"))
            if downloaded_files:
                print(f"\n📄 Downloaded files:")
                for file in downloaded_files:
                    size = file.stat().st_size
                    print(f"   📄 {file.name} ({size:,} bytes)")
            else:
                print(f"\n📁 No files found in {download_dir}")
        else:
            print(f"\n❌ Download failed!")
            print(f"💡 Note: If megatools is not installed, install it with:")
            print(f"   macOS: brew install megatools")
            print(f"   Ubuntu: sudo apt install megatools")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Test failed!")
        sys.exit(1) 