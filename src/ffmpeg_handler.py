#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SITG Video Trimmer - FFmpeg Handler
Handles FFmpeg operations for video trimming without re-encoding.
"""

import os
import sys
import subprocess
import platform
import json
import tempfile
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FFmpegHandler')


class FFmpegHandler:
    """Handles FFmpeg operations for video trimming."""
    
    # Class variable to track the current FFmpeg process
    current_process = None
    cancel_requested = False
    
    @classmethod
    def cancel_processing(cls):
        """Cancel the current FFmpeg process if one is running."""
        if cls.current_process is not None:
            logger.info("Cancelling FFmpeg process...")
            try:
                cls.cancel_requested = True
                cls.current_process.terminate()
                logger.info("FFmpeg process terminated")
                return True
            except Exception as e:
                logger.error(f"Error cancelling FFmpeg process: {str(e)}")
                return False
        return False
    
    @staticmethod
    def check_ffmpeg_installation():
        """
        Check if FFmpeg is installed and available.
        
        Returns:
            bool: True if FFmpeg is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    @staticmethod
    def get_video_metadata(video_path):
        """
        Get video metadata using FFmpeg.
        
        Args:
            video_path: Path to the video file
        
        Returns:
            dict: Dictionary containing video metadata
        """
        try:
            # Run ffprobe command to get video metadata in JSON format
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    video_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFprobe returned non-zero exit code: {result.returncode}")
                logger.error(f"FFprobe stderr: {result.stderr}")
                return None
            
            # Parse JSON output
            metadata = json.loads(result.stdout)
            
            # Extract relevant information
            video_info = {}
            
            # Find video stream
            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_info["width"] = stream.get("width")
                    video_info["height"] = stream.get("height")
                    video_info["codec"] = stream.get("codec_name")
                    
                    # Calculate frame rate
                    frame_rate = stream.get("r_frame_rate", "0/0")
                    if "/" in frame_rate:
                        num, den = map(int, frame_rate.split("/"))
                        if den != 0:
                            video_info["fps"] = num / den
                    
                    # Get duration
                    duration = stream.get("duration")
                    if duration is None:
                        duration = metadata.get("format", {}).get("duration")
                    
                    if duration:
                        video_info["duration"] = float(duration)
                    
                    break
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def remove_segments(video_path, output_path, segments, fade_duration=0.5, fast_mode=False):
        """
        Remove segments from a video using FFmpeg.
        
        Args:
            video_path: Path to the input video file
            output_path: Path for the output video file
            segments: List of (start_frame, end_frame) tuples representing segments to remove
            fade_duration: Duration of fade in/out in seconds
            fast_mode: If True, use stream copying for faster processing (no fades)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Processing video: {video_path}")
            logger.info(f"Output path: {output_path}")
            logger.info(f"Segments to remove: {segments}")
            logger.info(f"Fade duration: {fade_duration}")
            logger.info(f"Fast mode: {fast_mode}")
            
            # Get video metadata
            logger.info("Getting video metadata...")
            metadata = FFmpegHandler.get_video_metadata(video_path)
            if not metadata:
                logger.error("Failed to get video metadata")
                return False
            
            fps = metadata.get("fps", 30)  # Default to 30 fps if not found
            
            # Convert frame indices to time values
            time_segments = []
            for start_frame, end_frame in segments:
                start_time = start_frame / fps
                end_time = end_frame / fps
                time_segments.append((start_time, end_time))
            
            # Sort segments by start time
            time_segments.sort(key=lambda x: x[0])
            
            # Check if segments overlap
            logger.info(f"Time segments before merging: {time_segments}")
            for i in range(1, len(time_segments)):
                if time_segments[i][0] < time_segments[i-1][1]:
                    # Merge overlapping segments
                    logger.info(f"Merging overlapping segments: {time_segments[i-1]} and {time_segments[i]}")
                    time_segments[i-1] = (time_segments[i-1][0], max(time_segments[i-1][1], time_segments[i][1]))
                    time_segments[i] = None
            
            # Remove None entries (merged segments)
            time_segments = [seg for seg in time_segments if seg is not None]
            logger.info(f"Time segments after merging: {time_segments}")
            
            # Generate filter complex for removing segments
            filter_complex = []
            
            # Split the input into multiple parts
            input_parts = []
            current_time = 0
            
            for i, (start_time, end_time) in enumerate(time_segments):
                if start_time > current_time:
                    # Add the part before the segment to remove
                    input_parts.append((current_time, start_time))
                
                # Update current time to after the removed segment
                current_time = end_time
            
            # Add the final part after the last segment to remove
            if current_time < metadata.get("duration", 0):
                input_parts.append((current_time, metadata.get("duration", 0)))
            
            logger.info(f"Input parts to keep: {input_parts}")
            
            # Check if we have any parts to keep
            if len(input_parts) == 0:
                logger.error("No video segments to keep after processing")
                return False
            
            # Process differently based on mode
            if fast_mode:
                # Fast mode: Use segment concatenation without re-encoding
                return FFmpegHandler._fast_remove_segments(
                    video_path, output_path, input_parts, metadata
                )
            
            # Quality mode: Use filter complex with fades
            # Split the input into segments
            for i, (start_time, end_time) in enumerate(input_parts):
                # Ensure start and end times are valid
                if start_time >= end_time:
                    logger.error(f"Invalid time segment: start={start_time}, end={end_time}")
                    continue
                    
                # Add video filter
                filter_complex.append(f"[0:v]trim=start={start_time}:end={end_time},setpts=PTS-STARTPTS[v{i}]")
                
                # Check if audio stream exists (some videos might not have audio)
                try:
                    # Add audio filter
                    filter_complex.append(f"[0:a]atrim=start={start_time}:end={end_time},asetpts=PTS-STARTPTS[a{i}]")
                except Exception as e:
                    logger.warning(f"Could not add audio filter for segment {i}: {e}")
                
            # Count valid segments
            valid_segments = len([f for f in filter_complex if f.startswith("[0:v]trim=")])
            
            if valid_segments == 0:
                logger.error("No valid segments to process")
                return False
            
            # Concatenate the video segments
            v_parts = "".join(f"[v{i}]" for i in range(valid_segments))
            filter_complex.append(f"{v_parts}concat=n={valid_segments}:v=1:a=0[outv]")
            
            # Concatenate the audio segments if they exist
            a_parts = "".join(f"[a{i}]" for i in range(valid_segments))
            filter_complex.append(f"{a_parts}concat=n={valid_segments}:v=0:a=1[outa]")
                
            # Build the FFmpeg command
            # Note: We can't use -c:v copy with filter_complex
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-filter_complex", ";".join(filter_complex),
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",  # Use H.264 codec for video
                "-preset", "fast",  # Encoding preset (fast encoding)
                "-crf", "22",      # Constant Rate Factor (quality level, lower is better)
                "-c:a", "aac",     # Use AAC for audio
                "-b:a", "192k",    # Audio bitrate
                "-movflags", "+faststart",  # Optimize for web streaming
                "-y",              # Overwrite output file if it exists
                output_path
            ]
                
            # Log the full command for debugging
            logger.info(f"FFmpeg command: {' '.join(cmd)}")
            logger.info(f"Filter complex: {';'.join(filter_complex)}")
                
            # Run the FFmpeg command
            try:
                logger.info("Starting FFmpeg process...")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    universal_newlines=True
                )
                
                # Store the process in the class variable
                FFmpegHandler.current_process = process
                FFmpegHandler.cancel_requested = False
                
                # Wait for the process to complete with timeout
                try:
                    stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout
                    
                    # Check if the process was successful or cancelled
                    if FFmpegHandler.cancel_requested:
                        logger.info("FFmpeg process was cancelled by user")
                        success = False
                    else:
                        success = process.returncode == 0
                    
                    # Log the output
                    if success:
                        logger.info("FFmpeg process completed successfully")
                        # Verify the output file exists and has content
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            logger.info(f"Output file created successfully: {output_path} ({os.path.getsize(output_path)} bytes)")
                        else:
                            logger.error(f"Output file missing or empty: {output_path}")
                            success = False
                    else:
                        logger.error(f"FFmpeg process failed with return code {process.returncode}")
                        logger.error(f"FFmpeg stderr: {stderr}")
                except subprocess.TimeoutExpired:
                    # Kill the process if it times out
                    process.kill()
                    logger.error("FFmpeg process timed out after 10 minutes")
                    success = False
                finally:
                    # Clear the current process reference
                    FFmpegHandler.current_process = None
            except Exception as e:
                logger.error(f"Error executing FFmpeg command: {str(e)}", exc_info=True)
                success = False
                # Clear the current process reference
                FFmpegHandler.current_process = None
                
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing segments: {str(e)}", exc_info=True)
            # Clean up temporary directory if it exists
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False
    
    @staticmethod
    def _fast_remove_segments(video_path, output_path, input_parts, metadata):
        """
        Fast method to remove segments using FFmpeg's concat demuxer without re-encoding.
        
        Args:
            video_path: Path to the input video file
            output_path: Path for the output video file
            input_parts: List of (start_time, end_time) tuples representing parts to keep
            metadata: Video metadata dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Using fast processing mode with concat demuxer")
            
            # Create a temporary file list for the concat demuxer
            concat_file = os.path.join(temp_dir, "concat.txt")
            
            # Create temporary segment files
            segment_files = []
            
            for i, (start_time, end_time) in enumerate(input_parts):
                # Ensure start and end times are valid
                if start_time >= end_time:
                    logger.error(f"Invalid time segment: start={start_time}, end={end_time}")
                    continue
                
                # Calculate duration
                duration = end_time - start_time
                
                # Create output segment file
                segment_file = os.path.join(temp_dir, f"segment_{i}.mp4")
                segment_files.append(segment_file)
                
                # Build FFmpeg command to extract segment
                cmd = [
                    "ffmpeg",
                    "-ss", str(start_time),  # Start time
                    "-i", video_path,        # Input file
                    "-t", str(duration),     # Duration
                    "-c", "copy",            # Copy streams without re-encoding
                    "-avoid_negative_ts", "1",  # Shift timestamps to make them positive
                    "-y",                    # Overwrite output file
                    segment_file              # Output file
                ]
                
                logger.info(f"Extracting segment {i}: {start_time} to {end_time}")
                logger.info(f"FFmpeg command: {' '.join(cmd)}")
                
                # Run FFmpeg command
                logger.info("Starting FFmpeg segment extraction process...")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True
                )
                
                # Store the process in the class variable
                FFmpegHandler.current_process = process
                
                # Wait for the process to complete
                stdout, stderr = process.communicate()
                
                # Clear the current process reference
                FFmpegHandler.current_process = None
                
                # Check if the process was cancelled
                if FFmpegHandler.cancel_requested:
                    logger.info(f"Segment extraction {i} was cancelled by user")
                    return False
                
                # Check if the process was successful
                if process.returncode != 0:
                    logger.error(f"Failed to extract segment {i}: {stderr}")
                    return False
                
                # Verify segment file was created
                if not os.path.exists(segment_file) or os.path.getsize(segment_file) == 0:
                    logger.error(f"Segment file {segment_file} was not created or is empty")
                    return False
            
            # Create concat file
            with open(concat_file, 'w') as f:
                for segment_file in segment_files:
                    f.write(f"file '{segment_file}'\n")
            
            # Concatenate segments
            concat_cmd = [
                "ffmpeg",
                "-f", "concat",           # Use concat demuxer
                "-safe", "0",             # Don't require safe filenames
                "-i", concat_file,         # Input file list
                "-c", "copy",             # Copy streams without re-encoding
                "-y",                     # Overwrite output file
                output_path                # Output file
            ]
            
            logger.info(f"Concatenating segments with command: {' '.join(concat_cmd)}")
            
            # Run FFmpeg command
            logger.info("Starting FFmpeg concatenation process...")
            process = subprocess.Popen(
                concat_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Store the process in the class variable
            FFmpegHandler.current_process = process
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            # Clear the current process reference
            FFmpegHandler.current_process = None
            
            # Check if the process was cancelled
            if FFmpegHandler.cancel_requested:
                logger.info("Concatenation process was cancelled by user")
                success = False
            else:
                # Check if the process was successful
                success = process.returncode == 0
            
            # Log the output
            if success:
                logger.info("Fast processing completed successfully")
                # Verify the output file exists and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Output file created successfully: {output_path} ({os.path.getsize(output_path)} bytes)")
                else:
                    logger.error(f"Output file missing or empty: {output_path}")
                    success = False
            else:
                logger.error(f"Fast processing failed with return code {process.returncode}")
                logger.error(f"FFmpeg stderr: {process.stderr}")
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in fast processing: {str(e)}", exc_info=True)
            # Clean up temporary directory if it exists
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False
