#!/usr/bin/env python3
"""
Demo CLI Usage

This script demonstrates different ways to use the recreated mega module CLI interfaces
to download the provided file: https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI
"""

import subprocess
import sys
import os
from pathlib import Path

# Test URL
TEST_URL = "https://mega.nz/file/5r1nWZwK#DlBpWv2Hc0zLhjuldVF8ZJKepkBfZyNYPh7feSOA7jI"

def run_command(cmd, description):
    """Run a command and show the result"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    print("🚀 Mega Module CLI Demo")
    print("="*60)
    print(f"Test URL: {TEST_URL}")
    
    # Create demo directories
    dirs = ["./demo_simple", "./demo_universal", "./demo_verbose"]
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
    
    results = {}
    
    # Test 1: Simple Quick Test
    print(f"\n📋 Available CLI methods to test:")
    print(f"1. Quick Test Script (quick_test.py)")
    print(f"2. Mega CLI (mega_downloader_cli.py)")
    print(f"3. Universal Downloader CLI")
    print(f"4. Comprehensive Test Suite")
    
    # 1. Quick test
    results["Quick Test"] = run_command(
        [sys.executable, "quick_test.py"],
        "Testing Quick Download Script"
    )
    
    # 2. Mega CLI - Basic
    results["Mega CLI Basic"] = run_command(
        [sys.executable, "mega_downloader_cli.py", TEST_URL, "./demo_simple"],
        "Testing Mega CLI - Basic Download"
    )
    
    # 3. Mega CLI - Verbose
    results["Mega CLI Verbose"] = run_command(
        [sys.executable, "mega_downloader_cli.py", TEST_URL, "./demo_verbose", "-v"],
        "Testing Mega CLI - Verbose Mode"
    )
    
    # 4. Universal Downloader
    results["Universal Downloader"] = run_command(
        [sys.executable, "-m", "pyobidl.downloader", TEST_URL, "./demo_universal", "-v"],
        "Testing Universal Downloader CLI"
    )
    
    # 5. Comprehensive Test Suite
    results["Comprehensive Tests"] = run_command(
        [sys.executable, "test_mega_module.py"],
        "Running Comprehensive Test Suite"
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 CLI DEMO RESULTS")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"🎯 Overall: {passed}/{total} CLI tests successful ({passed/total*100:.1f}%)")
    
    # Show downloaded files
    print(f"\n📁 Downloaded files in demo directories:")
    for dir_path in dirs:
        files = list(Path(dir_path).glob("*"))
        if files:
            print(f"\n{dir_path}:")
            for file in files:
                size = file.stat().st_size if file.is_file() else "DIR"
                print(f"  📄 {file.name} ({size} bytes)" if size != "DIR" else f"  📁 {file.name}/")
        else:
            print(f"\n{dir_path}: (empty)")
    
    # Usage examples
    print(f"\n{'='*60}")
    print("💡 USAGE EXAMPLES")
    print(f"{'='*60}")
    
    print(f"""
🔸 Quick Download:
   python quick_test.py

🔸 Mega CLI (like your original script):
   python mega_downloader_cli.py "{TEST_URL}"
   python mega_downloader_cli.py "{TEST_URL}" ./downloads
   python mega_downloader_cli.py "{TEST_URL}" ./downloads -v

🔸 Universal Downloader (any platform):
   python -m pyobidl.downloader "{TEST_URL}" ./downloads
   python -m pyobidl.downloader "https://youtube.com/watch?v=..." ./downloads
   python -m pyobidl.downloader "https://mediafire.com/file/..." ./downloads

🔸 Full Test Suite:
   python test_mega_module.py

🔸 Python API Usage:
   from pyobidl.megacli.mega import Mega
   mega = Mega()
   mega.simple_download("{TEST_URL}", "./downloads")
""")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎉 Demo completed! At least some CLI methods work.")
    else:
        print(f"\n❌ Demo failed! None of the CLI methods worked.")
    
    print(f"\n💡 Tip: If downloads fail, try installing megatools:")
    print(f"   macOS: brew install megatools")
    print(f"   Ubuntu: sudo apt install megatools")
    
    sys.exit(0 if success else 1) 