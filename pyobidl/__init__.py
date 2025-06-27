"""
PyObidl - Python Online Binary Downloader Library

A universal downloader supporting multiple platforms:
- Mega.nz
- YouTube  
- MediaFire
- Google Drive

Usage:
    from pyobidl.megacli.mega import Mega
    from pyobidl.downloader import UniversalDownloader
    
    # Simple Mega download
    mega = Mega()
    mega.simple_download("https://mega.nz/file/...", "./downloads")
    
    # Universal downloader (auto-detects platform)
    downloader = UniversalDownloader()
    downloader.download("https://mega.nz/file/...", "./downloads")
"""

from .version import __version__

__all__ = [
    '__version__',
    'Mega',
    'UniversalDownloader',
    'YoutubeDownloader', 
    'MediaFireDownloader',
    'GoogleDriveDownloader'
]

# Optional: Import main classes for convenience
try:
    from .megacli.mega import Mega
    from .downloader import UniversalDownloader
    from .youtube import YoutubeDownloader
    from .mediafire import MediaFireDownloader
    from .googledrive import GoogleDriveDownloader
except ImportError:
    # Don't fail if dependencies are missing
    pass 