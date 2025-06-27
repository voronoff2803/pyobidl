#!/usr/bin/env python3
"""
Universal File Downloader

This script downloads files from various platforms including Mega.nz, YouTube, MediaFire, and Google Drive.
Usage: python downloader.py [url] [output_directory]
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from .megacli.mega import Mega
from .youtube import YoutubeDownloader
from .mediafire import MediaFireDownloader
from .googledrive import GoogleDriveDownloader
from .utils import setup_logging

logger = logging.getLogger(__name__)


class UniversalDownloader:
    def __init__(self):
        self.mega = Mega()
        self.youtube = YoutubeDownloader()
        self.mediafire = MediaFireDownloader()
        self.googledrive = GoogleDriveDownloader()

    def detect_platform(self, url):
        """
        Detect which platform the URL belongs to
        
        Args:
            url (str): The URL to analyze
            
        Returns:
            str: Platform name ('mega', 'youtube', 'mediafire', 'googledrive', 'unknown')
        """
        url = url.lower().strip()
        
        if 'mega.nz' in url or 'mega.co.nz' in url:
            return 'mega'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'mediafire.com' in url:
            return 'mediafire'
        elif 'drive.google.com' in url or 'docs.google.com' in url:
            return 'googledrive'
        else:
            return 'unknown'

    def download(self, url, output_dir=None):
        """
        Download file from any supported platform
        
        Args:
            url (str): URL to download from
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        platform = self.detect_platform(url)
        
        logger.info(f"🔍 Detected platform: {platform}")
        
        if platform == 'mega':
            return self.download_mega(url, output_dir)
        elif platform == 'youtube':
            return self.download_youtube(url, output_dir)
        elif platform == 'mediafire':
            return self.download_mediafire(url, output_dir)
        elif platform == 'googledrive':
            return self.download_googledrive(url, output_dir)
        else:
            logger.error(f"❌ Unsupported platform for URL: {url}")
            logger.info("📋 Supported platforms:")
            logger.info("  - Mega.nz: https://mega.nz/file/...")
            logger.info("  - YouTube: https://youtube.com/watch?v=...")
            logger.info("  - MediaFire: https://mediafire.com/file/...")
            logger.info("  - Google Drive: https://drive.google.com/file/d/...")
            return False

    def download_mega(self, url, output_dir=None):
        """
        Download file from Mega.nz
        
        Args:
            url (str): Mega.nz URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🚀 Starting Mega.nz download...")
            
            # Use the simple download method from the updated Mega class
            success = self.mega.simple_download(url, output_dir)
            
            if success:
                logger.info("✅ Mega.nz download completed successfully!")
            else:
                logger.error("❌ Mega.nz download failed!")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error downloading from Mega.nz: {e}")
            return False

    def download_youtube(self, url, output_dir=None):
        """
        Download video from YouTube
        
        Args:
            url (str): YouTube URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🚀 Starting YouTube download...")
            
            success = self.youtube.download(url, output_dir)
            
            if success:
                logger.info("✅ YouTube download completed successfully!")
            else:
                logger.error("❌ YouTube download failed!")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error downloading from YouTube: {e}")
            return False

    def download_mediafire(self, url, output_dir=None):
        """
        Download file from MediaFire
        
        Args:
            url (str): MediaFire URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🚀 Starting MediaFire download...")
            
            success = self.mediafire.download(url, output_dir)
            
            if success:
                logger.info("✅ MediaFire download completed successfully!")
            else:
                logger.error("❌ MediaFire download failed!")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error downloading from MediaFire: {e}")
            return False

    def download_googledrive(self, url, output_dir=None):
        """
        Download file from Google Drive
        
        Args:
            url (str): Google Drive URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🚀 Starting Google Drive download...")
            
            success = self.googledrive.download(url, output_dir)
            
            if success:
                logger.info("✅ Google Drive download completed successfully!")
            else:
                logger.error("❌ Google Drive download failed!")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error downloading from Google Drive: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Download files from various platforms (Mega.nz, YouTube, MediaFire, Google Drive)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python downloader.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4"
  python downloader.py "https://youtube.com/watch?v=dQw4w9WgXcQ" ./downloads
  python downloader.py "https://mediafire.com/file/abc123/example.zip"
  python downloader.py "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        """
    )
    
    parser.add_argument(
        'url',
        help='URL to download from (supports Mega.nz, YouTube, MediaFire, Google Drive)'
    )
    
    parser.add_argument(
        'output_dir',
        nargs='?',
        default=None,
        help='Output directory (optional, defaults to current directory)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    logger.info("🚀 Universal File Downloader")
    logger.info("=" * 50)
    logger.info(f"URL: {args.url}")
    
    downloader = UniversalDownloader()
    success = downloader.download(args.url, args.output_dir)
    
    if success:
        logger.info("\n✅ Download completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Download failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
