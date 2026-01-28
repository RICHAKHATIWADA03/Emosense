"""Video Processing Utilities"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import config

class VideoProcessor:
    def __init__(self, fps=None):
        self.fps = fps or config.VIDEO_FPS
        
    def validate_video(self, video_path):
        video_path = Path(video_path)
        if not video_path.exists():
            return False, "Video file not found", None
        if video_path.suffix.lower() not in config.SUPPORTED_VIDEO_FORMATS:
            return False, config.ERROR_MESSAGES['invalid_format'], None
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False, "Could not open video file", None
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            if duration > config.MAX_VIDEO_DURATION:
                return False, config.ERROR_MESSAGES['video_too_long'], duration
            if duration < 1:
                return False, "Video is too short (minimum 1 second)", duration
            return True, "Video is valid", duration
        except Exception as e:
            return False, f"Error validating video: {str(e)}", None
    
    def extract_frames(self, video_path):
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return frames
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / self.fps) if video_fps > 0 else 1
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            frame_count += 1
        cap.release()
        return frames
    
    def get_video_info(self, video_path):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {}
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return {
            'fps': fps, 'frame_count': frame_count, 'width': width,
            'height': height, 'duration': duration, 'resolution': f"{width}x{height}"
        }
