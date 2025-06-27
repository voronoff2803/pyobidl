#!/usr/bin/env python3
"""
Universal File Downloader

This script downloads files from various platforms including Mega.nz, YouTube, MediaFire, and Google Drive.
Includes backward-compatible Downloader class and new UniversalDownloader.
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path

from .megacli.mega import Mega
from .youtube import YoutubeDownloader
from .mediafire import MediaFireDownloader
from .googledrive import GoogleDriveDownloader
from .utils import setup_logging, ensure_dir_exists, get_url_file_name, makeSafeFilename, createID

logger = logging.getLogger(__name__)


class Downloader:
    """
    Backward-compatible Downloader class using new recreated mega module
    
    This maintains the old interface while using the improved backend.
    """
    def __init__(self, destpath='', mega_email=None, mega_password=None, proxies=None):
        self.filename = ''
        self.stoping = False
        self.destpath = destpath
        if self.destpath != '':
            ensure_dir_exists(self.destpath)
        self.id = createID(12)
        self.url = ''
        self.progressfunc = None
        self.args = None
        self.mega_email = mega_email
        self.mega_password = mega_password
        self.proxies = proxies
        
        # Initialize new downloaders
        self.mega = Mega()
        self.youtube = YoutubeDownloader()
        self.mediafire = MediaFireDownloader()
        self.googledrive = GoogleDriveDownloader()
        
    def detect_platform(self, url):
        """Detect which platform the URL belongs to"""
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
    
    def download_info(self, url='', proxies=None):
        """
        Get download information for a URL
        
        Args:
            url (str): URL to analyze
            proxies: Proxy settings (ignored, for compatibility)
            
        Returns:
            list: List of file information dictionaries
        """
        infos = []
        self.url = url
        
        platform = self.detect_platform(url)
        
        if platform == 'mega':
            try:
                # Use new mega module for URL parsing
                file_id, decryption_key = self.mega.parse_mega_url(url)
                if file_id and decryption_key:
                    # Try to get basic info
                    infos.append({
                        'fname': f'mega_file_{file_id}',
                        'furl': url,
                        'fsize': 0,  # Size unknown without download
                        'platform': 'mega'
                    })
                else:
                    logger.error("Invalid Mega URL format")
                    return None
            except Exception as e:
                logger.error(f"Mega download_info error: {str(e)}")
                return None
                
        elif platform in ['mediafire', 'googledrive', 'youtube']:
            # For other platforms, return basic info
            infos.append({
                'fname': f'{platform}_file',
                'furl': url,
                'fsize': 0,
                'platform': platform
            })
        else:
            logger.error(f"Unsupported platform for URL: {url}")
            return None
            
        return infos
    
    def download_url(self, url='', progressfunc=None, args=None, proxies=None):
        """
        Download file from URL using new recreated mega module
        
        Args:
            url (str): URL to download
            progressfunc: Progress callback function (for compatibility)
            args: Additional arguments (for compatibility)
            proxies: Proxy settings (for compatibility)
            
        Returns:
            str: Path to downloaded file if successful, None if failed
        """
        self.url = url
        self.progressfunc = progressfunc
        self.args = args
        
        if self.stoping:
            return None
            
        platform = self.detect_platform(url)
        
        try:
            if platform == 'mega':
                return self._download_mega(url)
            elif platform == 'mediafire':
                return self._download_mediafire(url)
            elif platform == 'googledrive':
                return self._download_googledrive(url)
            elif platform == 'youtube':
                return self._download_youtube(url)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return None
                
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return None
    
    def _download_mega(self, url):
        """Download from Mega using new recreated module"""
        try:
            logger.info(f"🔍 _download_mega: Starting download for URL: {url}")
            logger.info(f"🔍 _download_mega: Destination path: {self.destpath}")
            logger.info(f"🔍 _download_mega: Stopping flag: {self.stoping}")
            
            # Check if destination exists before download
            if not os.path.exists(self.destpath):
                logger.error(f"❌ _download_mega: Destination path does not exist: {self.destpath}")
                raise Exception(f"Destination path does not exist: {self.destpath}")
                
            # List files before download
            files_before = []
            if os.path.exists(self.destpath):
                files_before = [f for f in os.listdir(self.destpath) 
                              if os.path.isfile(os.path.join(self.destpath, f))]
                logger.info(f"🔍 _download_mega: Files before download: {files_before}")
            
            # Use the new simple download method
            logger.info(f"🔍 _download_mega: Calling mega.simple_download()")
            success = self.mega.simple_download(url, self.destpath)
            logger.info(f"🔍 _download_mega: simple_download returned: {success}")
            
            if not success:
                logger.error(f"❌ _download_mega: simple_download failed!")
                raise Exception("simple_download returned False")
            
            if self.stoping:
                logger.error(f"❌ _download_mega: Download was stopped!")
                raise Exception("Download was stopped")
                
            # Check if destination still exists after download
            if not os.path.exists(self.destpath):
                logger.error(f"❌ _download_mega: Destination path disappeared after download: {self.destpath}")
                raise Exception(f"Destination path disappeared: {self.destpath}")
                
            # Find the downloaded file
            files_after = [f for f in os.listdir(self.destpath) 
                          if os.path.isfile(os.path.join(self.destpath, f))]
            logger.info(f"🔍 _download_mega: Files after download: {files_after}")
            
            if not files_after:
                logger.error(f"❌ _download_mega: No files found in destination after download!")
                raise Exception("No files found in destination after download")
                
            # Return the most recently modified file
            try:
                latest_file = max(files_after, key=lambda f: os.path.getmtime(os.path.join(self.destpath, f)))
                full_path = os.path.join(self.destpath, latest_file)
                logger.info(f"✅ _download_mega: Latest file found: {latest_file}")
                logger.info(f"✅ _download_mega: Full path: {full_path}")
                
                # Verify file exists and has size
                if not os.path.exists(full_path):
                    logger.error(f"❌ _download_mega: Latest file path does not exist: {full_path}")
                    raise Exception(f"Latest file path does not exist: {full_path}")
                    
                file_size = os.path.getsize(full_path)
                logger.info(f"✅ _download_mega: File size: {file_size} bytes")
                
                if file_size == 0:
                    logger.error(f"❌ _download_mega: File has zero size!")
                    raise Exception("Downloaded file has zero size")
                
                logger.info(f"✅ _download_mega: Successfully returning: {full_path}")
                return full_path
                
            except Exception as file_error:
                logger.error(f"❌ _download_mega: Error processing files: {str(file_error)}")
                raise Exception(f"Error processing downloaded files: {str(file_error)}")
                        
        except Exception as e:
            logger.error(f"❌ _download_mega: Exception occurred: {str(e)}")
            logger.error(f"❌ _download_mega: Exception type: {type(e).__name__}")
            
            # Additional debugging info
            try:
                logger.error(f"🔍 _download_mega: Current destpath exists: {os.path.exists(self.destpath)}")
                if os.path.exists(self.destpath):
                    current_files = os.listdir(self.destpath)
                    logger.error(f"🔍 _download_mega: Current files in destpath: {current_files}")
            except Exception as debug_error:
                logger.error(f"🔍 _download_mega: Could not get debug info: {str(debug_error)}")
            
            # Re-raise the exception instead of returning None for debugging
            raise Exception(f"_download_mega failed: {str(e)}")
            # return None
    
    def _download_mediafire(self, url):
        """Download from MediaFire"""
        try:
            success = self.mediafire.download(url, self.destpath)
            if success and not self.stoping:
                return self._get_latest_file()
            return None
        except Exception as e:
            logger.error(f"MediaFire download error: {str(e)}")
            return None
    
    def _download_googledrive(self, url):
        """Download from Google Drive"""
        try:
            success = self.googledrive.download(url, self.destpath)
            if success and not self.stoping:
                return self._get_latest_file()
            return None
        except Exception as e:
            logger.error(f"Google Drive download error: {str(e)}")
            return None
    
    def _download_youtube(self, url):
        """Download from YouTube"""
        try:
            success = self.youtube.download(url, self.destpath)
            if success and not self.stoping:
                return self._get_latest_file()
            return None
        except Exception as e:
            logger.error(f"YouTube download error: {str(e)}")
            return None
    
    def _get_latest_file(self):
        """Get the most recently created file in destpath"""
        try:
            if os.path.exists(self.destpath):
                files = [f for f in os.listdir(self.destpath) 
                       if os.path.isfile(os.path.join(self.destpath, f))]
                if files:
                    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(self.destpath, f)))
                    return os.path.join(self.destpath, latest_file)
            return None
        except Exception:
            return None
    
    def stop(self):
        """Stop the downloader"""
        self.stoping = True
    
    def renove(self):
        """Retry download (legacy method name)"""
        return self.download_url(self.url, self.progressfunc, self.args)


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
