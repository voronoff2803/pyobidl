#!/usr/bin/env python3
"""
Docker Usage Example for Recreated PyObidl Mega Module

This example shows how to use the recreated mega module in a Docker environment.
"""

import os
import logging
from pyobidl.megacli.mega import Mega
from pyobidl.downloader import UniversalDownloader
from pyobidl.utils import setup_logging

def test_docker_environment():
    """Test that all components work in Docker"""
    
    # Setup logging
    setup_logging(verbose=True)
    logger = logging.getLogger(__name__)
    
    logger.info("🐳 Testing PyObidl in Docker environment")
    
    # Test 1: Check if megatools is available
    import shutil
    if shutil.which('megadl'):
        logger.info("✅ megatools (megadl) is available")
    else:
        logger.error("❌ megatools (megadl) not found!")
        return False
    
    # Test 2: Create mega instance
    try:
        mega = Mega()
        logger.info("✅ Mega instance created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create Mega instance: {e}")
        return False
    
    # Test 3: Test URL parsing
    test_url = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"
    file_id, key = mega.parse_mega_url(test_url)
    
    if file_id and key:
        logger.info(f"✅ URL parsing works: {file_id}")
    else:
        logger.error("❌ URL parsing failed")
        return False
    
    # Test 4: Universal downloader
    try:
        downloader = UniversalDownloader()
        platform = downloader.detect_platform(test_url)
        logger.info(f"✅ Universal downloader works, detected: {platform}")
    except Exception as e:
        logger.error(f"❌ Universal downloader failed: {e}")
        return False
    
    logger.info("🎉 All Docker environment tests passed!")
    return True

def download_mega_file(url, output_dir="/downloads"):
    """Download a file from Mega.nz in Docker environment"""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure download directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Use the simple download method
        mega = Mega()
        logger.info(f"🚀 Downloading: {url}")
        
        success = mega.simple_download(url, output_dir)
        
        if success:
            logger.info(f"✅ Download completed to: {output_dir}")
            
            # List downloaded files
            files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
            for file in files:
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                logger.info(f"📄 Downloaded: {file} ({size:,} bytes)")
                
            return True
        else:
            logger.error("❌ Download failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during download: {e}")
        return False

def download_universal(url, output_dir="/downloads"):
    """Download from any supported platform using Universal Downloader"""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure download directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Use universal downloader
        downloader = UniversalDownloader()
        platform = downloader.detect_platform(url)
        
        logger.info(f"🔍 Detected platform: {platform}")
        logger.info(f"🚀 Downloading: {url}")
        
        success = downloader.download(url, output_dir)
        
        if success:
            logger.info(f"✅ Universal download completed to: {output_dir}")
            return True
        else:
            logger.error("❌ Universal download failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during universal download: {e}")
        return False

if __name__ == "__main__":
    # Test Docker environment
    if test_docker_environment():
        print("🐳 Docker environment is ready for PyObidl!")
        
        # Example downloads
        test_url = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"
        
        # Download using simple method
        download_mega_file(test_url, "/tmp/downloads")
        
        # Download using universal method
        download_universal(test_url, "/tmp/universal_downloads")
    else:
        print("❌ Docker environment setup failed!") 