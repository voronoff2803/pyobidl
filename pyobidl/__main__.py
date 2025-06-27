#!/usr/bin/env python3
"""
PyObidl Package Main Entry Point

This allows running the package as a module:
python -m pyobidl [url] [output_dir]
"""

import sys
from .downloader import main

if __name__ == "__main__":
    main() 