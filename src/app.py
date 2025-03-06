#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SITG Video Trimmer - Main Application Controller
Integrates the VideoPlayer and Timeline components into a complete application.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import platform
from pathlib import Path

# Import local modules
from .video_player import VideoPlayer
from .timeline import Timeline


class SITGVideoTrimmerApp:
    """Main application controller for SITG Video Trimmer."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("SITG Video Trimmer")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize variables
        self.video_loaded = False
        self.fade_duration = tk.DoubleVar(value=0.5)  # Default fade duration: 0.5 seconds
        self.use_fast_processing = tk.BooleanVar(value=True)  # Default to fast processing
        
        # Create UI components
        self.create_video_area()
        self.create_timeline_area()
        self.create_controls_area()
        
        # Initialize video player and timeline
        self.video_player = VideoPlayer(self, self.video_canvas, self.timeline_canvas)
        self.timeline = Timeline(self.timeline_canvas, self.video_player)
        
        # Update button commands with timeline methods
        self.update_control_commands()
        
        # Create menu (after timeline is initialized)
        self.create_menu()
        
        # Bind keyboard shortcuts
        self.bind_keyboard_shortcuts()
        
        # Update layout when window is resized
        self.root.bind("<Configure>", self.on_window_resize)
    
    def create_menu(self):
        """Create the application menu bar."""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Video...", command=self.open_video, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Process Video...", command=self.process_video, accelerator="Ctrl+P")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Set Start Marker", command=lambda: self.timeline.add_marker('start'), accelerator="I")
        self.edit_menu.add_command(label="Set End Marker", command=lambda: self.timeline.add_marker('end'), accelerator="O")
        self.edit_menu.add_command(label="Delete Selected Marker", command=self.timeline.delete_marker, accelerator="Delete")
        self.edit_menu.add_command(label="Clear All Markers", command=self.timeline.clear_all_markers)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Help", command=self.show_help, accelerator="F1")
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def create_video_area(self):
        """Create the video display area."""
        # Create video frame
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create video canvas
        self.video_canvas = tk.Canvas(
            self.video_frame,
            bg="black",
            width=800,
            height=450
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
    
    def create_timeline_area(self):
        """Create the timeline area."""
        # Create timeline frame
        self.timeline_frame = ttk.Frame(self.main_frame)
        self.timeline_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create timeline canvas
        self.timeline_canvas = tk.Canvas(
            self.timeline_frame,
            bg="#333333",
            height=50
        )
        self.timeline_canvas.pack(fill=tk.X)
    
    def create_controls_area(self):
        """Create the controls area."""
        # Create controls frame
        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X)
        
        # Create playback controls
        self.playback_frame = ttk.Frame(self.controls_frame)
        self.playback_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Play/Pause button
        self.play_button = ttk.Button(
            self.playback_frame,
            text="Play",
            command=self.toggle_play
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Previous frame button
        self.prev_frame_button = ttk.Button(
            self.playback_frame,
            text="◀",
            command=lambda: self.video_player.show_frame(self.video_player.current_frame_index - 1)
        )
        self.prev_frame_button.pack(side=tk.LEFT, padx=5)
        
        # Next frame button
        self.next_frame_button = ttk.Button(
            self.playback_frame,
            text="▶",
            command=lambda: self.video_player.show_frame(self.video_player.current_frame_index + 1)
        )
        self.next_frame_button.pack(side=tk.LEFT, padx=5)
        
        # Frame counter label
        self.frame_counter = ttk.Label(
            self.playback_frame,
            text="Frame: 0 / 0"
        )
        self.frame_counter.pack(side=tk.LEFT, padx=20)
        
        # Time counter label
        self.time_counter = ttk.Label(
            self.playback_frame,
            text="Time: 00:00:00 / 00:00:00"
        )
        self.time_counter.pack(side=tk.LEFT, padx=20)
        
        # Create marker controls
        self.marker_frame = ttk.Frame(self.controls_frame)
        self.marker_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start marker button
        self.start_marker_button = ttk.Button(
            self.marker_frame,
            text="Set Start Marker (I)",
            command=lambda: None  # Placeholder, will be updated later
        )
        self.start_marker_button.pack(side=tk.LEFT, padx=5)
        
        # End marker button
        self.end_marker_button = ttk.Button(
            self.marker_frame,
            text="Set End Marker (O)",
            command=lambda: None  # Placeholder, will be updated later
        )
        self.end_marker_button.pack(side=tk.LEFT, padx=5)
        
        # Delete marker button
        self.delete_marker_button = ttk.Button(
            self.marker_frame,
            text="Delete Marker (Del)",
            command=lambda: None  # Placeholder, will be updated later
        )
        self.delete_marker_button.pack(side=tk.LEFT, padx=5)
        
        # Clear all markers button
        self.clear_markers_button = ttk.Button(
            self.marker_frame,
            text="Clear All Markers",
            command=lambda: None  # Placeholder, will be updated later
        )
        self.clear_markers_button.pack(side=tk.LEFT, padx=5)
        
        # Create processing controls
        self.processing_frame = ttk.Frame(self.controls_frame)
        self.processing_frame.pack(fill=tk.X)
        
        # Processing options frame
        options_frame = ttk.LabelFrame(self.processing_frame, text="Processing Options")
        options_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X)
        
        # Fast processing checkbox
        self.fast_processing_check = ttk.Checkbutton(
            options_frame,
            text="Fast Processing (No Fades)",
            variable=self.use_fast_processing
        )
        self.fast_processing_check.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=2)
        
        # Fade options frame (will be disabled when fast processing is selected)
        fade_frame = ttk.Frame(options_frame)
        fade_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # Fade duration label and entry
        ttk.Label(
            fade_frame,
            text="Fade Duration (seconds):"
        ).pack(side=tk.LEFT)
        
        self.fade_entry = ttk.Entry(
            fade_frame,
            textvariable=self.fade_duration,
            width=5
        )
        self.fade_entry.pack(side=tk.LEFT, padx=5)
        
        # Update fade frame state when fast processing option changes
        self.use_fast_processing.trace_add("write", lambda *args: self.update_fade_options())
        
        # Open video button
        self.open_video_button = ttk.Button(
            self.processing_frame,
            text="Open Video",
            command=self.open_video
        )
        self.open_video_button.pack(side=tk.RIGHT, padx=5)
        
        # Process video button
        self.process_button = ttk.Button(
            self.processing_frame,
            text="Process Video",
            command=self.process_video
        )
        self.process_button.pack(side=tk.RIGHT, padx=5)
    
    def update_control_commands(self):
        """Update button commands after timeline is initialized."""
        # Update marker button commands
        self.start_marker_button.config(command=lambda: self.timeline.add_marker('start'))
        self.end_marker_button.config(command=lambda: self.timeline.add_marker('end'))
        self.delete_marker_button.config(command=self.timeline.delete_marker)
        self.clear_markers_button.config(command=self.timeline.clear_all_markers)
    
    def bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts to functions."""
        self.root.bind("<Control-o>", lambda e: self.open_video())
        self.root.bind("<Control-p>", lambda e: self.process_video())
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Left>", lambda e: self.video_player.show_frame(self.video_player.current_frame_index - 1))
        self.root.bind("<Right>", lambda e: self.video_player.show_frame(self.video_player.current_frame_index + 1))
        self.root.bind("<i>", lambda e: self.timeline.add_marker('start'))
        self.root.bind("<o>", lambda e: self.timeline.add_marker('end'))
        self.root.bind("<Delete>", lambda e: self.timeline.delete_marker())
        self.root.bind("<Tab>", lambda e: self.timeline.select_next_marker())
        self.root.bind("<Shift-Tab>", lambda e: self.timeline.select_previous_marker())
        self.root.bind("<F1>", lambda e: self.show_help())
    
    def on_window_resize(self, event):
        """Handle window resize events."""
        # Update video display if a video is loaded
        if self.video_loaded and hasattr(self.video_player, 'current_frame_index'):
            self.video_player.show_frame(self.video_player.current_frame_index)
        
        # Update timeline visualization
        if hasattr(self.timeline, 'update_canvas_size'):
            self.timeline.update_canvas_size()
    
    def open_video(self):
        """Open a video file."""
        file_path = filedialog.askopenfilename(
            title="Open Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Update UI to show loading state
            self.root.config(cursor="watch")  # Use "watch" instead of "wait"
            self.root.update()
            
            try:
                # Load the video
                success = self.video_player.load_video(file_path)
                
                if success:
                    self.video_loaded = True
                    self.timeline.clear_all_markers()
                    self.update_ui_state()
                    self.root.title(f"SITG Video Trimmer - {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            finally:
                # Restore cursor
                self.root.config(cursor="")
    
    def toggle_play(self):
        """Toggle video playback."""
        if not self.video_loaded:
            return
        
        if self.video_player.playing:
            # If currently playing, pause the video
            self.video_player.pause()
            self.play_button.config(text="Play")
            print("Paused video playback")
        else:
            # If currently paused, start playing
            self.video_player.play()
            self.play_button.config(text="Pause")
            print("Started video playback")
    
    def update_fade_options(self):
        """Update fade options based on fast processing selection."""
        # Find the fade frame (parent of fade_entry)
        fade_frame = self.fade_entry.master
        
        # Enable/disable fade options based on fast processing selection
        if self.use_fast_processing.get():
            # Disable fade options when using fast processing
            for child in fade_frame.winfo_children():
                child.configure(state=tk.DISABLED)
        else:
            # Enable fade options when not using fast processing
            for child in fade_frame.winfo_children():
                child.configure(state=tk.NORMAL)
    
    def update_ui_state(self):
        """Update UI elements based on current state."""
        if self.video_loaded:
            # Enable video-related controls
            self.play_button.config(state=tk.NORMAL)
            self.prev_frame_button.config(state=tk.NORMAL)
            self.next_frame_button.config(state=tk.NORMAL)
            self.start_marker_button.config(state=tk.NORMAL)
            self.end_marker_button.config(state=tk.NORMAL)
            self.delete_marker_button.config(state=tk.NORMAL)
            self.clear_markers_button.config(state=tk.NORMAL)
            self.process_button.config(state=tk.NORMAL)
            
            # Update frame counter
            total_frames = self.video_player.total_frames
            current_frame = self.video_player.current_frame_index
            self.frame_counter.config(text=f"Frame: {current_frame} / {total_frames}")
            
            # Update time counter
            current_time = self.video_player.get_time_from_frame(current_frame)
            total_time = self.video_player.duration
            
            # Format time as HH:MM:SS
            current_time_str = self.format_time(current_time)
            total_time_str = self.format_time(total_time)
            
            self.time_counter.config(text=f"Time: {current_time_str} / {total_time_str}")
        else:
            # Disable video-related controls
            self.play_button.config(state=tk.DISABLED)
            self.prev_frame_button.config(state=tk.DISABLED)
            self.next_frame_button.config(state=tk.DISABLED)
            self.start_marker_button.config(state=tk.DISABLED)
            self.end_marker_button.config(state=tk.DISABLED)
            self.delete_marker_button.config(state=tk.DISABLED)
            self.clear_markers_button.config(state=tk.DISABLED)
            self.process_button.config(state=tk.DISABLED)
            
            # Reset counters
            self.frame_counter.config(text="Frame: 0 / 0")
            self.time_counter.config(text="Time: 00:00:00 / 00:00:00")
    
    def format_time(self, seconds):
        """Format time in seconds as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def process_video(self):
        """Process the video by removing the marked segments."""
        if not self.video_loaded or not self.video_player.video_path:
            messagebox.showwarning("No Video", "Please open a video file first.")
            return
        
        # Get segments for export
        segments = self.timeline.get_segments_for_export()
        
        if not segments:
            messagebox.showwarning("No Segments", "Please mark at least one segment to remove.")
            return
        
        # Ask for output file location
        input_file = self.video_player.video_path
        default_output = os.path.splitext(input_file)[0] + "_trimmed" + os.path.splitext(input_file)[1]
        
        output_file = filedialog.asksaveasfilename(
            title="Save Processed Video",
            initialfile=os.path.basename(default_output),
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("All files", "*.*")
            ]
        )
        
        if not output_file:
            return  # User cancelled
        
        # Get fade duration
        try:
            fade_duration = float(self.fade_duration.get())
            if fade_duration < 0:
                fade_duration = 0
        except ValueError:
            fade_duration = 0.5  # Default
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Processing Video")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Add progress label
        progress_label = ttk.Label(progress_window, text="Processing video...")
        progress_label.pack(pady=10)
        
        # Add progress bar
        progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        # Add cancel button
        cancel_button = ttk.Button(
            progress_window,
            text="Cancel",
            command=lambda: self.cancel_processing(progress_window)
        )
        cancel_button.pack(pady=10)
        
        # Get fast processing option
        use_fast_processing = self.use_fast_processing.get()
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(
            target=self.process_thread,
            args=(input_file, output_file, segments, fade_duration, progress_window, use_fast_processing)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def cancel_processing(self, progress_window):
        """Cancel the video processing operation."""
        try:
            # Import FFmpegHandler here to avoid circular imports
            from .ffmpeg_handler import FFmpegHandler
            import logging
            
            # Configure logging
            logger = logging.getLogger('VideoProcessing')
            logger.info("User requested cancellation of video processing")
            
            # Call the FFmpegHandler's cancel_processing method
            if FFmpegHandler.cancel_processing():
                # Update the progress window to show cancellation
                for widget in progress_window.winfo_children():
                    if isinstance(widget, ttk.Label):
                        widget.configure(text="Cancelling processing...")
                    if isinstance(widget, ttk.Button):
                        widget.configure(state="disabled")
            else:
                messagebox.showinfo("Information", "No active processing to cancel.")
                
        except Exception as e:
            print(f"Error cancelling processing: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def process_thread(self, input_file, output_file, segments, fade_duration, progress_window, use_fast_processing):
        """Thread function for video processing."""
        try:
            # Import FFmpegHandler here to avoid circular imports
            from .ffmpeg_handler import FFmpegHandler
            import logging
            
            # Configure logging
            logger = logging.getLogger('VideoProcessing')
            logger.info(f"Starting video processing: {input_file} -> {output_file}")
            logger.info(f"Segments to remove: {segments}")
            
            # Reset cancel flag at the start of processing
            FFmpegHandler.cancel_requested = False
            
            # Check if FFmpeg is installed
            if not FFmpegHandler.check_ffmpeg_installation():
                error_msg = "FFmpeg is not installed or not found in PATH. Please install FFmpeg to use this feature."
                logger.error(error_msg)
                self.root.after(0, lambda: self.on_process_complete(False, None, progress_window, error_msg))
                return
            
            # Process the video
            logger.info(f"Calling FFmpegHandler.remove_segments... (Fast mode: {use_fast_processing})")
            success = FFmpegHandler.remove_segments(
                input_file, output_file, segments, fade_duration, use_fast_processing
            )
            
            # Check if processing was cancelled
            if FFmpegHandler.cancel_requested:
                logger.info("Video processing was cancelled by user")
                self.root.after(0, lambda: self.on_process_complete(False, None, progress_window, "Processing cancelled by user", True))
            # Check if the output file was created and has a non-zero size
            elif success and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Video processing completed successfully: {output_file}")
                self.root.after(0, lambda: self.on_process_complete(success, output_file, progress_window))
            else:
                error_msg = "Video processing failed. The output file was not created or is empty."
                logger.error(error_msg)
                self.root.after(0, lambda: self.on_process_complete(False, None, progress_window, error_msg))
        except ImportError as e:
            error_msg = f"Failed to import required module: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: self.on_process_complete(False, None, progress_window, error_msg))
        except Exception as e:
            # Handle exceptions
            error_msg = f"Error during video processing: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.on_process_complete(False, None, progress_window, error_msg))
    
    def on_process_complete(self, success, output_path, progress_window, error_message=None, was_cancelled=False):
        """Handle completion of video processing."""
        # Reset FFmpegHandler cancel flag
        try:
            from .ffmpeg_handler import FFmpegHandler
            FFmpegHandler.cancel_requested = False
        except ImportError:
            pass
            
        # Close progress window
        progress_window.destroy()
        
        if success:
            result = messagebox.askyesno(
                "Processing Complete",
                f"Video processing completed successfully.\n\nOutput saved to: {output_path}\n\nWould you like to open the output folder?"
            )
            
            if result:
                # Open the output folder
                output_dir = os.path.dirname(output_path)
                if platform.system() == "Windows":
                    os.startfile(output_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", output_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", output_dir])
        elif was_cancelled:
            # Show a more friendly message for cancellation
            messagebox.showinfo("Processing Cancelled", "Video processing was cancelled.")
        else:
            error_msg = "An error occurred during video processing."
            if error_message:
                error_msg += f"\n\nError: {error_message}"
            
            messagebox.showerror("Processing Failed", error_msg)
    
    def show_about(self):
        """Show the about dialog."""
        about_text = """SITG Video Trimmer

A cross-platform application for trimming video files without re-encoding.

Version: 1.0.0

Developed for SITG (Stuff in the Game)

This application allows you to mark segments of a video for removal and process the video to remove those segments with smooth transitions."""
        
        messagebox.showinfo("About SITG Video Trimmer", about_text)
    
    def show_help(self):
        """Show the help dialog."""
        help_text = """SITG Video Trimmer Help

Basic Usage:
1. Open a video file (Ctrl+O)
2. Use the timeline to navigate through the video
3. Mark segments to remove:
   - Set start marker (I key) at the beginning of a segment to remove
   - Set end marker (O key) at the end of a segment to remove
4. Process the video (Ctrl+P) to create a new video with the marked segments removed

Keyboard Shortcuts:
- Ctrl+O: Open video file
- Ctrl+P: Process video
- Space: Play/Pause
- Left/Right arrows: Previous/Next frame
- I: Set start marker
- O: Set end marker
- Delete: Delete selected marker
- Tab: Select next marker
- Shift+Tab: Select previous marker
- F1: Show this help

Timeline Navigation:
- Click on the timeline to seek to a position
- Drag markers to adjust their positions
- The playhead (white line) shows the current position

Segments:
- Red areas on the timeline represent segments to be removed
- Green triangles mark the start points
- Red triangles mark the end points

Processing Options:
- Fade Duration: Length of the crossfade between cuts (in seconds)"""
        
        messagebox.showinfo("SITG Video Trimmer Help", help_text)
