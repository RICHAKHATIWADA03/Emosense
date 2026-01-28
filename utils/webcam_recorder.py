"""Webcam recorder - exact frame count for perfect sync"""
import cv2
import time
import streamlit as st
from pathlib import Path
import subprocess
import threading

def record_audio_only(audio_file, duration):
    """Record audio using ffmpeg"""
    cmd = [
        'ffmpeg',
        '-f', 'avfoundation',
        '-i', ':0',  # Audio device 0
        '-t', str(duration),
        '-y',
        str(audio_file)
    ]
    subprocess.run(cmd, capture_output=True)

def record_webcam_with_audio(output_path, duration=10, camera_index=0):
    """Record exact number of frames for perfect sync"""
    
    temp_video = str(output_path).replace('.mp4', '_video_only.mp4')
    temp_audio = str(output_path).replace('.mp4', '_audio.wav')
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None, f"Cannot access camera {camera_index}"
    
    fps = 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate EXACT number of frames needed
    total_frames = int(duration * fps)
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    # UI
    frame_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.info(f"🔴 Recording {total_frames} frames at {fps} fps = {duration}s")
    
    # Start audio recording
    audio_thread = threading.Thread(target=record_audio_only, args=(temp_audio, duration))
    audio_thread.start()
    
    # Small delay
    time.sleep(0.1)
    
    # Record EXACT number of frames
    start_time = time.time()
    
    for frame_num in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            st.warning(f"Camera read failed at frame {frame_num}")
            # Fill with last good frame if available
            continue
        
        out.write(frame)
        
        # Live preview (update every 5 frames to reduce overhead)
        if frame_num % 5 == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.circle(frame_rgb, (30, 30), 10, (255, 0, 0), -1)
            cv2.putText(frame_rgb, "REC", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            frame_placeholder.image(frame_rgb, channels="RGB", width=640)
        
        # Progress
        progress = (frame_num + 1) / total_frames
        elapsed = time.time() - start_time
        remaining = duration - int(elapsed)
        
        progress_bar.progress(progress)
        status_text.markdown(f"### ⏱️ {remaining}s | Frame {frame_num+1}/{total_frames}")
        
        # Pace the recording to match real time
        target_time = start_time + ((frame_num + 1) / fps)
        current_time = time.time()
        sleep_time = target_time - current_time
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    cap.release()
    out.release()
    
    # Wait for audio
    audio_thread.join(timeout=duration + 5)
    
    frame_placeholder.empty()
    progress_bar.empty()
    status_text.empty()
    
    actual_duration = time.time() - start_time
    st.info(f" Recorded {total_frames} frames in {actual_duration:.2f}s (target: {duration}s)")
    
    # Check files
    if not Path(temp_video).exists():
        return None, "Video file not created"
    if not Path(temp_audio).exists():
        return None, "Audio file not created"
    
    # Get actual durations with ffprobe
    try:
        video_probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', temp_video],
            capture_output=True, text=True
        )
        audio_probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', temp_audio],
            capture_output=True, text=True
        )
        
        video_dur = float(video_probe.stdout.strip())
        audio_dur = float(audio_probe.stdout.strip())
        st.info(f" Video: {video_dur:.2f}s | Audio: {audio_dur:.2f}s")
    except:
        pass
    
    # Merge - use video as master timeline
    st.info(" Merging with video as master timeline...")
    merge_cmd = [
        'ffmpeg',
        '-i', temp_video,
        '-i', temp_audio,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',  # Use video from first input
        '-map', '1:a:0',  # Use audio from second input
        '-shortest',      # End when shortest stream ends
        '-y',
        str(output_path)
    ]
    
    try:
        result = subprocess.run(merge_cmd, capture_output=True, timeout=60)
        
        # Cleanup
        Path(temp_video).unlink(missing_ok=True)
        Path(temp_audio).unlink(missing_ok=True)
        
        if result.returncode == 0 and Path(output_path).exists():
            st.success("Video is ready for analysis")
            return str(output_path), None
        else:
            error = result.stderr.decode() if result.stderr else "Unknown"
            return None, f"Merge failed: {error}"
            
    except Exception as e:
        Path(temp_video).unlink(missing_ok=True)
        Path(temp_audio).unlink(missing_ok=True)
        return None, f"Error: {str(e)}"
