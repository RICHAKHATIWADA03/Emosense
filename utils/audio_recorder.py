"""Audio-only recorder from microphone"""
import subprocess
import time
import streamlit as st
from pathlib import Path

def record_audio_from_mic(output_path, duration=10):
    """Record audio only from microphone"""
    
    cmd = [
        'ffmpeg',
        '-f', 'avfoundation',
        '-i', ':0',  # Audio device 0 (microphone)
        '-t', str(duration),
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        str(output_path)
    ]
    
    # UI
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.info(f"🎤 Recording audio for {duration} seconds... Speak clearly!")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - int(elapsed)
            progress = elapsed / duration
            
            progress_bar.progress(min(progress, 1.0))
            status_text.markdown(f"### 🔴 Recording... {remaining}s remaining")
            time.sleep(0.1)
        
        # Wait for process
        process.wait(timeout=5)
        
        progress_bar.empty()
        status_text.empty()
        
        if process.returncode == 0 and Path(output_path).exists():
            st.success("✅ Audio recording complete!")
            return str(output_path), None
        else:
            stderr = process.stderr.read().decode() if process.stderr else "Unknown error"
            return None, f"Recording failed: {stderr}"
            
    except Exception as e:
        return None, f"Error: {str(e)}"
