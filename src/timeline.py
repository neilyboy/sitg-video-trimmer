#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Timeline Component for SITG Video Trimmer
"""

import tkinter as tk
from tkinter import messagebox


class Timeline:
    """Timeline component for displaying video progress and markers."""
    
    def __init__(self, canvas, video_player):
        """
        Initialize the timeline.
        
        Args:
            canvas: Tkinter canvas for the timeline
            video_player: VideoPlayer instance
        """
        self.canvas = canvas
        self.video_player = video_player
        self.segments = []  # List of (start, end) tuples in seconds
        self.markers = []   # List of {'type': 'start'/'end', 'time': seconds, 'segment_id': int}
        self.selected_marker = None  # Index of selected marker in self.markers
        self.dragging = False
        self.drag_marker_index = -1
        
        # Timeline dimensions
        self.timeline_height = 30
        self.marker_height = 15
        self.time_label_height = 20
        
        # Timeline colors
        self.timeline_bg_color = "#333333"
        self.timeline_fg_color = "#555555"
        self.playhead_color = "#FFFFFF"
        self.segment_color = "#FF0000"
        self.start_marker_color = "#00FF00"
        self.end_marker_color = "#FF0000"
        
        # Initialize the timeline visual elements
        self.canvas.delete("all")
        self.timeline_bg = self.canvas.create_rectangle(
            0, 0, self.canvas.winfo_reqwidth(), self.timeline_height,
            fill=self.timeline_bg_color, outline=""
        )
        
        self.playhead = self.canvas.create_line(
            0, 0, 0, self.timeline_height,
            fill=self.playhead_color, width=2
        )
        
        # Bind mouse events to the canvas
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        
        # Initialize with empty timeline
        self.update_canvas_size()
    
    def update_canvas_size(self):
        """Update the timeline based on the current canvas size."""
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        height = self.canvas.winfo_height() or self.canvas.winfo_reqheight()
        
        # Update timeline background
        self.canvas.coords(
            self.timeline_bg,
            0, 0, width, self.timeline_height
        )
        
        # Redraw time markers
        self.draw_time_markers()
        
        # Update segments visualization
        self.update_segments_visualization()
    
    def draw_time_markers(self):
        """Draw time markers on the timeline."""
        if not self.video_player.duration:
            return
        
        # Clear existing time markers
        self.canvas.delete("time_marker")
        
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        
        # Determine appropriate interval for time markers
        duration = self.video_player.duration
        
        if duration <= 60:  # Less than a minute
            interval = 10  # Every 10 seconds
        elif duration <= 300:  # Less than 5 minutes
            interval = 30  # Every 30 seconds
        elif duration <= 1800:  # Less than 30 minutes
            interval = 60  # Every minute
        else:
            interval = 300  # Every 5 minutes
        
        # Draw the markers
        for t in range(0, int(duration) + interval, interval):
            if t > duration:
                break
                
            x = int((t / duration) * width)
            
            # Draw marker line
            self.canvas.create_line(
                x, 0, x, self.timeline_height,
                fill="#777777", width=1, tags="time_marker"
            )
            
            # Draw time label
            minutes, seconds = divmod(t, 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours > 0:
                time_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                time_str = f"{int(minutes):02d}:{int(seconds):02d}"
                
            self.canvas.create_text(
                x, self.timeline_height + 10,
                text=time_str, fill="white", tags="time_marker",
                font=("Arial", 8)
            )
    
    def update_playhead_position(self, time_position):
        """
        Update the playhead position based on the current time.
        
        Args:
            time_position: Current time position in seconds
        """
        if not self.video_player.duration:
            return
            
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        x = (time_position / self.video_player.duration) * width
        
        self.canvas.coords(
            self.playhead,
            x, 0, x, self.timeline_height
        )
    
    def update_segments_visualization(self):
        """Update the visualization of all segments and markers on the timeline."""
        # Clear existing segment visualizations
        self.canvas.delete("segment")
        self.canvas.delete("marker")
        
        if not self.video_player.duration:
            return
            
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        
        # Draw all segments
        for i, (start, end) in enumerate(self.segments):
            # Convert times to x coordinates
            start_x = (start / self.video_player.duration) * width
            end_x = (end / self.video_player.duration) * width
            
            # Draw segment rectangle
            self.canvas.create_rectangle(
                start_x, 0, end_x, self.timeline_height,
                fill=self.segment_color, outline="", tags=f"segment segment_{i}"
            )
        
        # Draw all markers
        for i, marker in enumerate(self.markers):
            marker_time = marker['time']
            marker_type = marker['type']
            segment_id = marker['segment_id']
            
            # Convert time to x coordinate
            x = (marker_time / self.video_player.duration) * width
            
            # Determine marker color
            color = self.start_marker_color if marker_type == 'start' else self.end_marker_color
            
            # Draw marker triangle
            self.canvas.create_polygon(
                x - 5, 0,
                x + 5, 0,
                x, self.marker_height,
                fill=color, outline="",
                tags=f"marker marker_{i} {marker_type}_{segment_id}"
            )
            
            # Highlight selected marker
            if self.selected_marker == i:
                self.canvas.create_rectangle(
                    x - 6, 0,
                    x + 6, self.marker_height + 1,
                    outline="white", width=2,
                    tags=f"marker marker_{i} {marker_type}_{segment_id}"
                )
    
    def time_to_x(self, time_position):
        """Convert a time position to an x coordinate on the timeline."""
        if not self.video_player.duration:
            return 0
            
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        return (time_position / self.video_player.duration) * width
    
    def x_to_time(self, x_position):
        """Convert an x coordinate on the timeline to a time position."""
        if not self.video_player.duration:
            return 0
            
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        return (x_position / width) * self.video_player.duration
    
    def on_click(self, event):
        """Handle mouse click events on the timeline."""
        if not self.video_player.duration:
            return
            
        # Check if click is on a marker
        items = self.canvas.find_withtag("marker")
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("marker_"):
                    marker_index = int(tag.split("_")[1])
                    x1, y1, x2, y2 = self.canvas.bbox(item)
                    if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                        self.dragging = True
                        self.drag_marker_index = marker_index
                        self.selected_marker = marker_index
                        self.update_segments_visualization()
                        return
        
        # If not on a marker, seek to the clicked position
        time_position = self.x_to_time(event.x)
        frame_index = self.video_player.get_frame_at_time(time_position)
        self.video_player.show_frame(frame_index)
        self.update_playhead_position(time_position)
    
    def on_drag(self, event):
        """Handle mouse drag events on the timeline."""
        if not self.dragging or not self.video_player.duration or self.drag_marker_index < 0:
            return
            
        time_position = self.x_to_time(event.x)
        
        # Ensure time is within video bounds
        time_position = max(0, min(time_position, self.video_player.duration))
        
        # Update marker position
        marker = self.markers[self.drag_marker_index]
        marker_type = marker['type']
        segment_id = marker['segment_id']
        
        # Find the paired marker (start or end) in the same segment
        paired_marker_index = None
        paired_time = None
        
        for i, m in enumerate(self.markers):
            if i != self.drag_marker_index and m['segment_id'] == segment_id:
                if (marker_type == 'start' and m['type'] == 'end') or \
                   (marker_type == 'end' and m['type'] == 'start'):
                    paired_marker_index = i
                    paired_time = m['time']
                    break
        
        # Apply constraints based on marker type
        if marker_type == 'start' and paired_time is not None:
            # Start marker can't go beyond end marker
            time_position = min(time_position, paired_time - 0.1)
        elif marker_type == 'end' and paired_time is not None:
            # End marker can't go before start marker
            time_position = max(time_position, paired_time + 0.1)
        
        # Update marker time
        marker['time'] = time_position
        
        # Update corresponding segment
        for i, (start, end) in enumerate(self.segments):
            if i == segment_id:
                if marker_type == 'start':
                    self.segments[i] = (time_position, end)
                else:  # end
                    self.segments[i] = (start, time_position)
                break
        
        # Update visualization
        self.update_segments_visualization()
        
        # Update video frame
        frame_index = self.video_player.get_frame_at_time(time_position)
        self.video_player.show_frame(frame_index)
        self.update_playhead_position(time_position)
    
    def on_release(self, event):
        """Handle mouse release events on the timeline."""
        self.dragging = False
        self.drag_marker_index = -1
    
    def add_marker(self, marker_type):
        """Add a marker at the current playhead position."""
        if not self.video_player.duration:
            return False
        
        current_time = self.video_player.get_time_from_frame(self.video_player.current_frame_index)
        
        # Validate marker type
        if marker_type not in ['start', 'end']:
            return False
        
        # Find if there's a corresponding marker to pair with
        if marker_type == 'start':
            # Look for an unpaired end marker
            for i, marker in enumerate(self.markers):
                if marker['type'] == 'end' and marker['segment_id'] == -1:
                    # Found an unpaired end marker
                    segment_id = len(self.segments)
                    
                    # Create a new segment
                    self.segments.append((current_time, marker['time']))
                    
                    # Update the end marker's segment_id
                    marker['segment_id'] = segment_id
                    
                    # Add the start marker
                    self.markers.append({
                        'type': 'start',
                        'time': current_time,
                        'segment_id': segment_id
                    })
                    
                    self.selected_marker = len(self.markers) - 1
                    self.update_segments_visualization()
                    return True
            
            # No unpaired end marker found, create a new start marker
            self.markers.append({
                'type': 'start',
                'time': current_time,
                'segment_id': -1  # Not paired yet
            })
            
            self.selected_marker = len(self.markers) - 1
            self.update_segments_visualization()
            return True
            
        else:  # marker_type == 'end'
            # Look for an unpaired start marker
            for i, marker in enumerate(self.markers):
                if marker['type'] == 'start' and marker['segment_id'] == -1:
                    # Found an unpaired start marker
                    segment_id = len(self.segments)
                    
                    # Ensure end time is after start time
                    if current_time <= marker['time']:
                        messagebox.showwarning("Invalid End Point", "End point must be after start point")
                        return False
                    
                    # Create a new segment
                    self.segments.append((marker['time'], current_time))
                    
                    # Update the start marker's segment_id
                    marker['segment_id'] = segment_id
                    
                    # Add the end marker
                    self.markers.append({
                        'type': 'end',
                        'time': current_time,
                        'segment_id': segment_id
                    })
                    
                    self.selected_marker = len(self.markers) - 1
                    self.update_segments_visualization()
                    return True
            
            # No unpaired start marker found, create a new end marker
            self.markers.append({
                'type': 'end',
                'time': current_time,
                'segment_id': -1  # Not paired yet
            })
            
            self.selected_marker = len(self.markers) - 1
            self.update_segments_visualization()
            return True
    
    def delete_marker(self, marker_index=None):
        """Delete a marker at the specified index or the currently selected marker."""
        if marker_index is None and self.selected_marker < 0:
            return False
        
        index_to_delete = marker_index if marker_index is not None else self.selected_marker
        
        if index_to_delete < 0 or index_to_delete >= len(self.markers):
            return False
        
        marker = self.markers[index_to_delete]
        segment_id = marker['segment_id']
        marker_type = marker['type']
        
        # If marker is part of a segment, remove the segment and both markers
        if segment_id >= 0:
            # Find the paired marker
            paired_marker_index = None
            for i, m in enumerate(self.markers):
                if i != index_to_delete and m['segment_id'] == segment_id:
                    paired_marker_index = i
                    break
            
            # Remove the segment
            if segment_id < len(self.segments):
                self.segments.pop(segment_id)
            
            # Update segment IDs for all markers with higher segment IDs
            for m in self.markers:
                if m['segment_id'] > segment_id:
                    m['segment_id'] -= 1
            
            # Remove both markers (delete the higher index first to avoid index shifting)
            if paired_marker_index is not None:
                if paired_marker_index > index_to_delete:
                    self.markers.pop(paired_marker_index)
                    self.markers.pop(index_to_delete)
                else:
                    self.markers.pop(index_to_delete)
                    self.markers.pop(paired_marker_index)
            else:
                # Just in case there's no paired marker (shouldn't happen in normal operation)
                self.markers.pop(index_to_delete)
        else:
            # Marker is not part of a segment, just remove it
            self.markers.pop(index_to_delete)
        
        # Reset selection if the selected marker was deleted
        if self.selected_marker == index_to_delete:
            self.selected_marker = -1
        elif self.selected_marker > index_to_delete:
            self.selected_marker -= 1
        
        self.update_segments_visualization()
        return True
    
    def get_segments_for_export(self):
        """Return segments in a format suitable for export or processing."""
        # Sort segments by start time
        sorted_segments = sorted(self.segments, key=lambda x: x[0])
        
        # Convert time values to frame indices for precise trimming
        frame_segments = []
        for start_time, end_time in sorted_segments:
            start_frame = self.video_player.get_frame_at_time(start_time)
            end_frame = self.video_player.get_frame_at_time(end_time)
            frame_segments.append((start_frame, end_frame))
        
        return frame_segments
    
    def clear_all_markers(self):
        """Clear all markers and segments."""
        self.markers = []
        self.segments = []
        self.selected_marker = -1
        self.update_segments_visualization()
        return True
    
    def select_next_marker(self):
        """Select the next marker in the timeline."""
        if not self.markers:
            return False
        
        if self.selected_marker < 0:
            self.selected_marker = 0
        else:
            self.selected_marker = (self.selected_marker + 1) % len(self.markers)
        
        # Update visualization to show selected marker
        self.update_segments_visualization()
        
        # Move playhead to selected marker position
        marker = self.markers[self.selected_marker]
        time_position = marker['time']
        frame_index = self.video_player.get_frame_at_time(time_position)
        self.video_player.show_frame(frame_index)
        self.update_playhead_position(time_position)
        
        return True
    
    def select_previous_marker(self):
        """Select the previous marker in the timeline."""
        if not self.markers:
            return False
        
        if self.selected_marker < 0:
            self.selected_marker = len(self.markers) - 1
        else:
            self.selected_marker = (self.selected_marker - 1) % len(self.markers)
        
        # Update visualization to show selected marker
        self.update_segments_visualization()
        
        # Move playhead to selected marker position
        marker = self.markers[self.selected_marker]
        time_position = marker['time']
        frame_index = self.video_player.get_frame_at_time(time_position)
        self.video_player.show_frame(frame_index)
        self.update_playhead_position(time_position)
        
        return True
