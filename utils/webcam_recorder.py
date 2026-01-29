"""Webcam recorder for Streamlit Cloud - Browser-based recording"""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import base64
import tempfile

def record_webcam_cloud(output_path, duration=15):
    """
    Record video using browser's MediaRecorder API
    Works on Streamlit Cloud (records in user's browser)
    """
    
    st.markdown("### 📹 Browser-Based Recording")
    st.info(f"🎥 Recording will be {duration} seconds. Click 'Start Recording' below.")
    
    # HTML/JavaScript for browser-based recording
    recorder_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            #videoPreview {{
                width: 100%;
                max-width: 640px;
                background: black;
                border-radius: 10px;
            }}
            .button-container {{
                margin: 20px 0;
                display: flex;
                gap: 10px;
            }}
            button {{
                padding: 12px 24px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }}
            #startBtn {{
                background-color: #FF4B4B;
                color: white;
            }}
            #startBtn:hover {{
                background-color: #E04343;
            }}
            #startBtn:disabled {{
                background-color: #CCCCCC;
                cursor: not-allowed;
            }}
            .status {{
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-weight: bold;
            }}
            .recording {{
                background-color: #FFE5E5;
                color: #FF4B4B;
            }}
            .ready {{
                background-color: #E5F5E5;
                color: #00AA00;
            }}
            .countdown {{
                font-size: 48px;
                font-weight: bold;
                color: #FF4B4B;
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <video id="videoPreview" autoplay muted></video>
        
        <div class="button-container">
            <button id="startBtn">🔴 Start Recording ({duration}s)</button>
        </div>
        
        <div id="status"></div>
        <div id="countdown"></div>
        
        <script>
            const videoPreview = document.getElementById('videoPreview');
            const startBtn = document.getElementById('startBtn');
            const statusDiv = document.getElementById('status');
            const countdownDiv = document.getElementById('countdown');
            
            let mediaRecorder;
            let recordedChunks = [];
            let stream;
            const recordingDuration = {duration} * 1000; // Convert to milliseconds
            
            // Initialize camera
            async function initCamera() {{
                try {{
                    stream = await navigator.mediaDevices.getUserMedia({{
                        video: {{ width: 1280, height: 720 }},
                        audio: true
                    }});
                    videoPreview.srcObject = stream;
                    statusDiv.innerHTML = '<div class="status ready"> Camera ready. Click "Start Recording" to begin.</div>';
                }} catch (err) {{
                    statusDiv.innerHTML = '<div class="status" style="background-color: #FFE5E5; color: #FF4B4B;"> Camera access denied. Please allow camera and microphone permissions.</div>';
                    console.error('Camera error:', err);
                }}
            }}
            
            // Start recording
            async function startRecording() {{
                if (!stream) {{
                    alert('Camera not initialized');
                    return;
                }}
                
                recordedChunks = [];
                
                // Create MediaRecorder
                const options = {{ mimeType: 'video/webm;codecs=vp9' }};
                try {{
                    mediaRecorder = new MediaRecorder(stream, options);
                }} catch (e) {{
                    // Fallback to default codec
                    mediaRecorder = new MediaRecorder(stream);
                }}
                
                mediaRecorder.ondataavailable = (event) => {{
                    if (event.data.size > 0) {{
                        recordedChunks.push(event.data);
                    }}
                }};
                
                mediaRecorder.onstop = () => {{
                    const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                    uploadVideo(blob);
                }};
                
                // Start recording
                mediaRecorder.start();
                startBtn.disabled = true;
                
                // Show countdown
                let remaining = {duration};
                statusDiv.innerHTML = '<div class="status recording">🔴 Recording in progress...</div>';
                
                const countdownInterval = setInterval(() => {{
                    countdownDiv.textContent = remaining;
                    remaining--;
                    
                    if (remaining < 0) {{
                        clearInterval(countdownInterval);
                        countdownDiv.textContent = '';
                    }}
                }}, 1000);
                
                // Auto-stop after duration
                setTimeout(() => {{
                    clearInterval(countdownInterval);
                    if (mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop();
                        statusDiv.innerHTML = '<div class="status">⏳ Processing video...</div>';
                    }}
                }}, recordingDuration);
            }}
            
            // Upload video to Streamlit
            function uploadVideo(blob) {{
                const reader = new FileReader();
                reader.onloadend = () => {{
                    const base64data = reader.result.split(',')[1];
                    
                    // Send to Streamlit via postMessage
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: base64data
                    }}, '*');
                    
                    statusDiv.innerHTML = '<div class="status ready"> Recording complete! Video uploaded.</div>';
                    startBtn.disabled = false;
                    startBtn.textContent = '🔴 Record Again';
                }};
                reader.readAsDataURL(blob);
            }}
            
            // Event listeners
            startBtn.addEventListener('click', startRecording);
            
            // Initialize on load
            initCamera();
        </script>
    </body>
    </html>
    """
    
    # Render the recorder component
    video_data = components.html(recorder_html, height=700)
    
    if video_data:
        st.success(" Video received from browser!")
        
        # Decode base64 video data
        try:
            video_bytes = base64.b64decode(video_data)
            
            # Save to output path
            with open(output_path, 'wb') as f:
                f.write(video_bytes)
            
            st.success(f" Video saved to {output_path}")
            return str(output_path), None
            
        except Exception as e:
            return None, f"Error saving video: {str(e)}"
    
    return None, None


def record_webcam_with_audio(output_path, duration=15, camera_index=0):
    """
    Wrapper function to maintain compatibility with existing code
    Redirects to a cloud-compatible browser recording
    """
    return record_webcam_cloud(output_path, duration)


# Alternative: Simple frame capture (if you just need photos)
def capture_photo_cloud():
    """Capture a single photo using browser camera"""
    st.markdown("### 📸 Photo Capture")
    
    picture = st.camera_input("Take a photo")
    
    if picture:
        # Save the photo
        photo_path = Path(tempfile.gettempdir()) / f"photo_{int(time.time())}.jpg"
        with open(photo_path, 'wb') as f:
            f.write(picture.getvalue())
        
        st.success(f"Photo saved!")
        return str(photo_path)
    
    return None
