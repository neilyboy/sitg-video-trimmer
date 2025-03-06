#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SITG Video Trimmer
A cross-platform application for trimming video files without re-encoding.
This is a compatibility launcher script for the modular version of SITG Video Trimmer.

Features:
- Load and display video files (MKV, MP4, TS formats)
- Visual timeline representation of the video's duration
- Mark segments for removal with start/end points
- Multiple segment marking capabilities
- Fade in/out transitions at segment boundaries
- Two processing modes: Fast (no re-encoding) and Quality (with re-encoding)
- Cancellable processing with progress feedback
- Cross-platform compatibility (Windows, macOS, and Linux)
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main module from the src package
try:
    from src.main import main
    
    if __name__ == "__main__":
        print("Starting SITG Video Trimmer...")
        sys.exit(main())
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("\nMake sure you have installed all required dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
