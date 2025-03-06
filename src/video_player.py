#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Player Component for SITG Video Trimmer
"""

import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import os
import platform
import queue
import subprocess


class VideoPlayer:
    """Video player component that handles video loading and frame extraction."""
    
    def __init__(self, master, video_canvas, timeline_canvas):
        """
        Initialize the video player.
        
        Args:
            master: The parent widget
            video_canvas: Tkinter canvas for displaying video frames
            timeline_canvas: Tkinter canvas for displaying the timeline
        """
        self.master = master
        self.video_canvas = video_canvas
        self.timeline_canvas = timeline_canvas
        
        self.cap = None
        self.video_path = None
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        self.current_frame_index = 0
        self.frame_width = 0
        self.frame_height = 0
        self.playing = False
        self.play_thread = None
        
        # Display message on video canvas
        self.video_canvas.create_text(
            self.video_canvas.winfo_reqwidth() // 2,
            self.video_canvas.winfo_reqheight() // 2,
            text="No video loaded",
            fill="white",
            font=("Arial", 14)
        )
    
    def load_video(self, video_path):
        """
        Load a video file and initialize video properties.
        
        Args:
            video_path: Path to the video file
        
        Returns:
            bool: True if video loaded successfully, False otherwise
        """
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.duration = self.total_frames / self.fps if self.fps else 0
            self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Close previous video if open
            if self.cap is not None:
                self.cap.release()
            
            # Set new video
            self.cap = cap
            self.video_path = video_path
            self.current_frame_index = 0
            self.playing = False
            
            # Show first frame
            self.show_frame(0)
            
            return True
            
        except Exception as e:
            print(f"Error loading video: {str(e)}")
            return False
    
    def show_frame(self, frame_index):
        """
        Display the frame at the specified index.
        
        Args:
            frame_index: Index of the frame to display
        
        Returns:
            bool: True if frame displayed successfully, False otherwise
        """
        if self.cap is None or frame_index < 0 or frame_index >= self.total_frames:
            return False
        
        # Skip setting frame position if we're just moving to the next frame
        # This is a major optimization for sequential playback
        if frame_index != self.current_frame_index + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        
        # Read the frame
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        # Update current frame index
        self.current_frame_index = frame_index
        
        # Get canvas dimensions
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.video_canvas.winfo_reqwidth()
            canvas_height = self.video_canvas.winfo_reqheight()
        
        # Only recalculate display dimensions if canvas size changed
        if not hasattr(self, '_last_canvas_size') or self._last_canvas_size != (canvas_width, canvas_height):
            self._last_canvas_size = (canvas_width, canvas_height)
            
            # Calculate aspect ratio
            frame_aspect = self.frame_width / self.frame_height
            canvas_aspect = canvas_width / canvas_height
            
            if frame_aspect > canvas_aspect:
                self._display_width = canvas_width
                self._display_height = int(canvas_width / frame_aspect)
            else:
                self._display_height = canvas_height
                self._display_width = int(canvas_height * frame_aspect)
        
        # During playback, use the fastest resize method (INTER_NEAREST)
        # During frame-by-frame navigation, use higher quality (INTER_LINEAR)
        interp_method = cv2.INTER_NEAREST if self.playing else cv2.INTER_LINEAR
        
        # Resize frame - use fastest method during playback
        frame = cv2.resize(frame, (self._display_width, self._display_height), 
                          interpolation=interp_method)
        
        # Convert frame from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create PhotoImage - use the fastest method available
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        
        # Minimize canvas operations
        self.video_canvas.delete("all")
        
        # Create image on canvas
        self.video_canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=photo, anchor=tk.CENTER
        )
        
        # Keep a reference to prevent garbage collection
        self.video_canvas.image = photo
        
        # Only show time text during frame-by-frame navigation or every 10 frames during playback
        if not self.playing or frame_index % 10 == 0:
            # Display time position
            time_position = self.get_time_from_frame(frame_index)
            minutes, seconds = divmod(time_position, 60)
            hours, minutes = divmod(minutes, 60)
            
            time_text = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            self.video_canvas.create_text(
                10, 10,
                text=time_text,
                fill="white",
                font=("Arial", 10),
                anchor=tk.NW
            )
        
        # Only update timeline during frame-by-frame navigation
        # Skip timeline updates during playback for better performance
        if not self.playing and hasattr(self.master, 'timeline') and self.master.timeline:
            self.master.timeline.update_playhead_position(self.get_time_from_frame(frame_index))
        
        return True
    
    def get_frame_at_time(self, time_position):
        """
        Get the frame index corresponding to a time position.
        
        Args:
            time_position: Time position in seconds
        
        Returns:
            int: Frame index
        """
        if self.fps == 0:
            return 0
            
        frame_index = int(time_position * self.fps)
        return max(0, min(frame_index, self.total_frames - 1))
    
    def get_time_from_frame(self, frame_index):
        """
        Get the time position corresponding to a frame index.
        
        Args:
            frame_index: Frame index
        
        Returns:
            float: Time position in seconds
        """
        if self.fps == 0:
            return 0
            
        return frame_index / self.fps
    
    def play(self):
        """Start video playback."""
        if self.cap is None:
            print("Cannot play: No video loaded")
            return
            
        if self.playing:
            print("Already playing")
            return
        
        print(f"Starting playback at frame {self.current_frame_index} of {self.total_frames}")
        print(f"FPS: {self.fps}")
        
        # Set playing flag to True
        self.playing = True
        
        # Pre-calculate frame timing
        self.frame_time_ms = int(1000 / self.fps) if self.fps > 0 else 33  # ms per frame
        
        # Start simple playback using Tkinter's after method
        # This avoids threading issues and is more reliable
        self._schedule_next_frame()
        
        print("Playback started")
    
    def _schedule_next_frame(self):
        """Schedule the next frame for display."""
        if not self.playing or self.cap is None:
            return
        
        # If we've reached the end of the video, stop playback
        if self.current_frame_index >= self.total_frames - 1:
            self.playing = False
            if hasattr(self.master, 'update_ui_state'):
                self.master.update_ui_state()
            return
        
        # Calculate next frame index
        next_frame = self.current_frame_index + 1
        
        # Display the frame
        try:
            # Start timing the frame display
            start_time = time.time()
            
            # Show the frame
            success = self.show_frame(next_frame)
            if not success:
                print(f"Failed to show frame {next_frame}")
                self.playing = False
                if hasattr(self.master, 'update_ui_state'):
                    self.master.update_ui_state()
                return
            
            # Calculate how long it took to display the frame
            processing_time = time.time() - start_time
            processing_time_ms = int(processing_time * 1000)
            
            # Calculate the delay for the next frame
            # If processing took longer than frame time, use minimal delay
            delay = max(1, self.frame_time_ms - processing_time_ms)
            
            # Log performance every 100 frames
            if next_frame % 100 == 0:
                print(f"Frame {next_frame}: Processing time {processing_time_ms}ms, Target frame time {self.frame_time_ms}ms")
            
            # Schedule the next frame
            if self.playing:
                self.master.root.after(delay, self._schedule_next_frame)
                
        except Exception as e:
            print(f"Error displaying frame: {str(e)}")
            self.playing = False
            if hasattr(self.master, 'update_ui_state'):
                self.master.update_ui_state()
    
    def _display_frame(self, frame_index):
        """Display a frame and handle any errors."""
        try:
            if not self.playing:
                return
                
            self.show_frame(frame_index)
        except Exception as e:
            print(f"Error displaying frame: {str(e)}")
            self.playing = False
            if hasattr(self.master, 'update_ui_state'):
                self.master.update_ui_state()
    
    def _safe_show_frame(self, frame_index):
        """Safely show a frame on the main UI thread."""
        if not self.playing:
            return
            
        try:
            self.show_frame(frame_index)
        except Exception as e:
            print(f"Error showing frame: {str(e)}")
            self.playing = False
    
    def pause(self):
        """Pause video playback."""
        if not self.playing:
            return
            
        print(f"Pausing video at frame {self.current_frame_index}")
        
        # Set playing flag to False to stop the playback loop
        self.playing = False
        
        # Update UI if needed
        if hasattr(self.master, 'update_ui_state'):
            self.master.update_ui_state()
            
        print("Video paused")
