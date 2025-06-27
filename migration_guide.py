#!/usr/bin/env python3
"""
Migration Guide: Old Downloader to New Recreated Mega Module

This shows the exact code changes needed to migrate from the old system.
"""

# OLD CODE (what you were trying to use):
"""
extract_folder = "temp"
dl = Downloader(destpath=extract_folder)
"""

# NEW CODE - Option 1: Universal Downloader (Recommended)
def new_way_universal():
    from pyobidl.downloader import UniversalDownloader
    
    extract_folder = "temp"
    dl = UniversalDownloader()
    
    # Usage:
    # success = dl.download(url, extract_folder)
    return dl, extract_folder

# NEW CODE - Option 2: Direct Mega (like your original script)
def new_way_mega_only():
    from pyobidl.megacli.mega import Mega
    
    extract_folder = "temp"
    mega = Mega()
    
    # Usage:
    # success = mega.simple_download(url, extract_folder)
    return mega, extract_folder

# COMPLETE MIGRATION EXAMPLE
def complete_example():
    """Complete example showing old vs new"""
    
    # ============ OLD WAY ============
    # from pyobidl.downloader import Downloader
    # 
    # extract_folder = "temp"
    # dl = Downloader(destpath=extract_folder)
    # result = dl.download_url(url)
    # infos = dl.download_info(url)
    
    # ============ NEW WAY ============
    from pyobidl.downloader import UniversalDownloader
    from pyobidl.megacli.mega import Mega
    import os
    
    extract_folder = "temp"
    os.makedirs(extract_folder, exist_ok=True)
    
    # Method 1: Universal (recommended)
    dl = UniversalDownloader()
    
    # Download any URL (auto-detects platform)
    def download_universal(url):
        return dl.download(url, extract_folder)
    
    # Get platform info
    def get_info_universal(url):
        platform = dl.detect_platform(url)
        return {'platform': platform}
    
    # Method 2: Mega-specific (fast for mega URLs)
    mega = Mega()
    
    def download_mega(url):
        return mega.simple_download(url, extract_folder)
    
    def get_info_mega(url):
        file_id, key = mega.parse_mega_url(url)
        return {'file_id': file_id, 'key': key}
    
    return {
        'universal_downloader': dl,
        'mega_downloader': mega,
        'extract_folder': extract_folder,
        'download_universal': download_universal,
        'download_mega': download_mega,
        'get_info_universal': get_info_universal,
        'get_info_mega': get_info_mega
    }

# SIMPLE DIRECT REPLACEMENT
def simple_replacement():
    """The simplest way to replace your code"""
    
    # Your old line:
    # extract_folder = "temp"
    # dl = Downloader(destpath=extract_folder)
    
    # Replace with:
    extract_folder = "temp"
    from pyobidl.downloader import UniversalDownloader
    import os
    
    os.makedirs(extract_folder, exist_ok=True)
    dl = UniversalDownloader()
    
    # Now instead of: dl.download_url(url)
    # Use: dl.download(url, extract_folder)
    
    return dl, extract_folder

if __name__ == "__main__":
    print("🔄 Migration Guide: Old Downloader → New System")
    print("="*60)
    
    print("\n📋 DIRECT REPLACEMENT:")
    print("OLD: extract_folder = 'temp'")
    print("     dl = Downloader(destpath=extract_folder)")
    print()
    print("NEW: extract_folder = 'temp'")
    print("     dl = UniversalDownloader()")
    print("     os.makedirs(extract_folder, exist_ok=True)")
    
    print("\n📋 METHOD REPLACEMENTS:")
    print("OLD: dl.download_url(url)")
    print("NEW: dl.download(url, extract_folder)")
    print()
    print("OLD: dl.download_info(url)")
    print("NEW: dl.detect_platform(url)")
    
    print("\n📋 EXAMPLE USAGE:")
    
    # Test the simple replacement
    try:
        dl, extract_folder = simple_replacement()
        print(f"✅ UniversalDownloader created successfully!")
        print(f"📁 Extract folder: {extract_folder}")
        
        # Test URL detection
        test_url = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"
        platform = dl.detect_platform(test_url)
        print(f"🔍 Platform detection test: {platform}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n💡 MIGRATION TIPS:")
    print("• UniversalDownloader works with Mega, YouTube, MediaFire, Google Drive")
    print("• For Mega-only usage, use Mega().simple_download() for better performance")
    print("• Progress tracking is now via logging: setup_logging(verbose=True)")
    print("• The new system is more reliable and faster for Mega downloads")
    
    print(f"\n🎯 YOUR EXACT REPLACEMENT:")
    print(f"Replace this:")
    print(f'    extract_folder = "temp"')
    print(f'    dl = Downloader(destpath=extract_folder)')
    print(f"")
    print(f"With this:")
    print(f'    extract_folder = "temp"')
    print(f'    import os')
    print(f'    from pyobidl.downloader import UniversalDownloader')
    print(f'    os.makedirs(extract_folder, exist_ok=True)')
    print(f'    dl = UniversalDownloader()') 