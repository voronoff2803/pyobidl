#!/usr/bin/env python3
"""
Mega.nz File Downloader CLI

This script downloads files from Mega.nz using the pyobidl mega module.
Usage: python mega_downloader_cli.py [mega_url] [output_directory]
"""

import os
import sys
import argparse
import logging

# Add the pyobidl directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyobidl'))

from pyobidl.megacli.mega import Mega
from pyobidl.utils import setup_logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download files from Mega.nz using the pyobidl mega module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mega_downloader_cli.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4"
  python mega_downloader_cli.py "https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4" ./downloads
        """
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        default='https://mega.nz/file/B3kg2ZqC#aEOZ5e6OJYV-H8aKFY8nWhX-wxwZQL21hlWV1Sj9jg4',
        help='Mega.nz file URL'
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
    
    parser.add_argument(
        '--login',
        action='store_true',
        help='Use authenticated login (requires MEGA_EMAIL and MEGA_PASSWORD env vars)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    logger.info("🚀 Mega.nz File Downloader")
    logger.info("=" * 50)
    logger.info(f"URL: {args.url}")
    
    try:
        # Create Mega instance
        mega = Mega()
        
        # Login if requested
        if args.login:
            email = os.getenv('MEGA_EMAIL')
            password = os.getenv('MEGA_PASSWORD')
            
            if email and password:
                logger.info("🔐 Logging in with credentials...")
                mega.login(email, password)
                logger.info("✅ Login successful!")
            else:
                logger.warning("⚠️  MEGA_EMAIL and MEGA_PASSWORD environment variables not set. Using anonymous login.")
                mega.login()
        
        # Download the file
        logger.info("🚀 Starting download...")
        success = mega.simple_download(args.url, args.output_dir)
        
        if success:
            logger.info("\n✅ Download completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Download failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Download interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 