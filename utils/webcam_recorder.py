"""
LIVE Webcam Recording for Streamlit Cloud using streamlit-webrtc
This records video+audio LIVE from browser - works on cloud!
"""

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import cv2
import numpy as np
from pathlib import Path
import threading
import queue
import time
import tempfile

# WebRTC configuration for Streamlit Cloud
# RTC_CONFIGURATION = RTCConfiguration({
#     "iceServers": [
#         {"urls": ["stun:stun.l.google.com:19302"]},
#         {"urls": ["stun:stun1.l.google.com:19302"]},
#     ]
# })
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)


class VideoRecorder:
    """Records video frames and audio from WebRTC stream"""
    
    def __init__(self, output_path, fps=30):
        self.output_path = output_path
        self.fps = fps
        self.video_frames = []
        self.audio_frames = []
        self.is_recording = False
        self.lock = threading.Lock()
        self.frame_count = 0
        
    def start_recording(self):
        """Start recording"""
        with self.lock:
            self.is_recording = True
            self.video_frames = []
            self.audio_frames = []
            self.frame_count = 0
            
    def stop_recording(self):
        """Stop recording and save video"""
        with self.lock:
            self.is_recording = False
        
        if len(self.video_frames) > 0:
            return self._save_video()
        return None
    
    def add_video_frame(self, frame):
        """Add video frame to buffer"""
        with self.lock:
            if self.is_recording:
                # Convert to BGR for OpenCV
                img = frame.to_ndarray(format="bgr24")
                self.video_frames.append(img)
                self.frame_count += 1
    
    def add_audio_frame(self, frame):
        """Add audio frame to buffer"""
        with self.lock:
            if self.is_recording:
                self.audio_frames.append(frame)
    
    def _save_video(self):
        """Save recorded frames to video file"""
        if len(self.video_frames) == 0:
            return None
        
        # Get frame dimensions
        height, width = self.video_frames[0].shape[:2]
        
        # Create temporary video file
        temp_video = str(self.output_path).replace('.mp4', '_temp.mp4')
        
        # Write video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, self.fps, (width, height))
        
        for frame in self.video_frames:
            out.write(frame)
        
        out.release()
        
        # If we have audio, merge it
        if len(self.audio_frames) > 0:
            return self._merge_audio_video(temp_video)
        else:
            # No audio, just rename
            Path(temp_video).rename(self.output_path)
            return self.output_path
    
    def _merge_audio_video(self, video_path):
        """Merge audio and video using ffmpeg"""
        import subprocess
        
        # Save audio to temporary file
        temp_audio = str(self.output_path).replace('.mp4', '_temp.wav')
        
        try:
            # Write audio frames
            import wave
            with wave.open(temp_audio, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(48000)  # Sample rate
                
                for frame in self.audio_frames:
                    wav_file.writeframes(frame.to_ndarray().tobytes())
            
            # Merge using ffmpeg
            subprocess.run([
                'ffmpeg', '-i', video_path, '-i', temp_audio,
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', str(self.output_path)
            ], check=True, capture_output=True)
            
            # Cleanup
            Path(video_path).unlink(missing_ok=True)
            Path(temp_audio).unlink(missing_ok=True)
            
            return self.output_path
            
        except Exception as e:
            st.error(f"Audio merge failed: {e}")
            # Return video without audio
            Path(video_path).rename(self.output_path)
            return self.output_path


def record_webcam_live(output_path, duration=15):
    """
    Record LIVE video with audio from browser webcam
    Works on Streamlit Cloud!
    
    Args:
        output_path: Path to save video
        duration: Recording duration in seconds
        
    Returns:
        (video_path, error)
    """
    
    st.markdown("### 📹 Live Webcam Recording")
    st.info(f"🎥 Recording will be {duration} seconds with audio")
    
    # Initialize recorder
    if 'recorder' not in st.session_state:
        st.session_state.recorder = VideoRecorder(output_path, fps=30)
    
    # Recording state
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
        st.session_state.start_time = None
        st.session_state.video_path = None
    
    # Video frame callback
    def video_frame_callback(frame):
        if st.session_state.is_recording:
            st.session_state.recorder.add_video_frame(frame)
            
            # Add recording indicator
            img = frame.to_ndarray(format="bgr24")
            cv2.circle(img, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(img, "REC", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 0, 255), 2)
            
            # Check if duration reached
            elapsed = time.time() - st.session_state.start_time
            if elapsed >= duration:
                st.session_state.is_recording = False
                st.session_state.video_path = st.session_state.recorder.stop_recording()
            
            return av.VideoFrame.from_ndarray(img, format="bgr24")
        
        return frame
    
    # Audio frame callback
    def audio_frame_callback(frame):
        if st.session_state.is_recording:
            st.session_state.recorder.add_audio_frame(frame)
        return frame
    
    # # WebRTC streamer
    # ctx = webrtc_streamer(
    #     key="live-recorder",
    #     mode=WebRtcMode.SENDRECV,
    #     rtc_configuration=RTC_CONFIGURATION,
    #     video_frame_callback=video_frame_callback,
    #     audio_frame_callback=audio_frame_callback,
    #     media_stream_constraints={
    #         "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}},
    #         "audio": True
    #     },
    #     async_processing=True,
    # )
    webrtc_ctx = webrtc_streamer(
        key="emotion-detector",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        async_processing=True,
    )
    
    # Recording controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Start Recording", disabled=st.session_state.is_recording):
            if ctx.state.playing:
                st.session_state.is_recording = True
                st.session_state.start_time = time.time()
                st.session_state.recorder.start_recording()
                st.rerun()
            else:
                st.error("Please start the webcam first!")
    
    with col2:
        if st.button("⏹️ Stop Recording", disabled=not st.session_state.is_recording):
            st.session_state.is_recording = False
            st.session_state.video_path = st.session_state.recorder.stop_recording()
            st.rerun()
    
    # Show recording status
    if st.session_state.is_recording:
        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, duration - elapsed)
        
        progress = elapsed / duration
        st.progress(progress)
        st.markdown(f"### ⏱️ Recording: {elapsed}s / {duration}s (Remaining: {remaining}s)")
        
        # Auto-refresh to update countdown
        time.sleep(0.5)
        st.rerun()
    
    # Show result
    if st.session_state.video_path:
        st.success(" Recording complete!")
        
        # Show video preview
        if Path(st.session_state.video_path).exists():
            st.video(st.session_state.video_path)
            
            # Reset button
            if st.button("🔄 Record Again"):
                st.session_state.video_path = None
                st.session_state.is_recording = False
                st.rerun()
            
            return str(st.session_state.video_path), None
    
    return None, None


# Simplified wrapper for compatibility with your existing code
def record_webcam_with_audio(output_path, duration=15, camera_index=0):
    """
    Compatibility wrapper - redirects to live recording
    
    Args:
        output_path: Path to save video
        duration: Recording duration in seconds  
        camera_index: Ignored (uses browser camera)
        
    Returns:
        (video_path, error)
    """
    return record_webcam_live(output_path, duration)
