#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SITG Video Trimmer - Main Entry Point
Launches the SITG Video Trimmer application.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Import local modules
from .app import SITGVideoTrimmerApp
from .ffmpeg_handler import FFmpegHandler


def main():
    """Main entry point for the application."""
    # Check FFmpeg installation
    if not FFmpegHandler.check_ffmpeg_installation():
        print("Error: FFmpeg is required but not found on your system.")
        print("Please install FFmpeg and try again.")
        if sys.platform.startswith('win'):
            print("Windows: https://ffmpeg.org/download.html")
        elif sys.platform == 'darwin':
            print("macOS: brew install ffmpeg")
        else:
            print("Linux: sudo apt-get install ffmpeg")
        return 1
    
    # Create the Tkinter root window
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        if sys.platform.startswith('win'):
            root.iconbitmap(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico'))
        else:
            # For Linux and macOS
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png')
            if os.path.exists(icon_path):
                icon_img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon_img)
    except Exception:
        # Ignore icon errors
        pass
    
    # Initialize the application
    app = SITGVideoTrimmerApp(root)
    
    # Start the main event loop
    root.mainloop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
