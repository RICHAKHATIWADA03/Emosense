"""EmoSense - Complete with Authentication, History, Advanced Metrics, and Subscriptions"""
import streamlit as st
import streamlit.components.v1 as components
import torch
from pathlib import Path
from datetime import datetime
import config
from auth import check_authentication, login_page, logout
from history_page import show_history_page
from subscription_page import show_subscription_page
from subscription_utils import get_user_limits, check_recording_limit, check_upload_limit, check_history_limit, show_upgrade_prompt
from database import save_analysis
from models import load_cross_attention_model
from models.visual_encoder import VisualEncoder
from models.audio_encoder import AudioEncoder
from models.text_encoder import TextEncoder
from utils import (VideoProcessor, AudioProcessor, EmotionVisualizer, 
                   WordLevelEmotionAnalyzer, generate_video_report, 
                   generate_audio_report, AdvancedMetricsCalculator,
                   export_to_json, export_to_csv, get_export_bytes)
from utils.webcam_recorder import record_webcam_with_audio
from utils.audio_recorder import record_audio_from_mic

st.set_page_config(page_title=config.PAGE_TITLE, page_icon=config.PAGE_ICON, 
                   layout=config.LAYOUT)
st.write('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"/>', unsafe_allow_html=True)

# Check authentication
if not check_authentication():
    login_page()
    st.stop()

with st.sidebar:
    user = st.session_state.user

    st.markdown(
        f'<i class="fa-solid fa-circle-user"></i> <b>{user["username"]}</b>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<i class="fa-solid fa-envelope"></i> {user["email"]}',
        unsafe_allow_html=True
    )

    st.markdown("---")

    tier = user.get("subscription_tier", "free")

    if tier == "premium":
        st.markdown(
            '<i class="fa-solid fa-star" style="color: gold;"></i> Premium',
            unsafe_allow_html=True
        )
    else:
        st.markdown("<i class=\"fa-solid fa-f\" style=\"color: gray;\"></i> Free", unsafe_allow_html=True)

    st.markdown("---")
    
    page = st.radio("Navigation", ["📝 Analyze", "⏳ History", "💎 Subscription"], label_visibility="collapsed")
    
    st.markdown("---")
    
    if st.button("➜] Logout"):
        logout()

# Show selected page
if page == "⏳ History":
    show_history_page()
    st.stop()
elif page == "💎 Subscription":
    show_subscription_page()
    st.stop()

# Continue with main analysis page
@st.cache_resource
def load_models():
    fusion_model = load_cross_attention_model()
    visual_encoder = VisualEncoder()
    audio_encoder = AudioEncoder()
    text_encoder = TextEncoder()
    word_analyzer = WordLevelEmotionAnalyzer()
    metrics_calc = AdvancedMetricsCalculator()
    return fusion_model, visual_encoder, audio_encoder, text_encoder, word_analyzer, metrics_calc

@st.cache_resource
def load_processors():
    return VideoProcessor(), AudioProcessor(), EmotionVisualizer()

def process_video(video_path, fusion_model, visual_encoder, audio_encoder, text_encoder,
                  video_processor, audio_processor, visualizer, word_analyzer):
    results = {'success': False, 'error': None, 'mode': 'video'}
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Extracting frames...")
        progress_bar.progress(10)
        frames = video_processor.extract_frames(video_path)
        video_info = video_processor.get_video_info(video_path)
        if not frames:
            results['error'] = "No frames extracted"
            return results
        
        status_text.text("Processing audio...")
        progress_bar.progress(25)
        audio_results = audio_processor.process_video(video_path)
        
        status_text.text("Analyzing facial expressions...")
        progress_bar.progress(45)
        visual_results = visual_encoder.analyze_video_frames(frames)
        
        status_text.text("Analyzing voice...")
        progress_bar.progress(60)
        if audio_results['audio_path']:
            audio_emotion_results = audio_encoder.analyze_audio(audio_results['audio_path'])
        else:
            audio_emotion_results = {
                'features': torch.ones(1, 4) / 4,
                'audio_emotions_7': {e: 1.0/7 for e in config.EMOTION_LABELS},
                'dominant_emotion': 'neutral'
            }
        
        status_text.text("Analyzing text...")
        progress_bar.progress(75)
        text_content = audio_results['transcript']['text'] if audio_results['transcript']['text'] else "No speech"
        text_results = text_encoder.analyze_text(text_content)
        
        status_text.text("Analyzing word-level emotions...")
        progress_bar.progress(85)
        word_emotions = word_analyzer.highlight_transcript(text_content) if text_content != "No speech" else []
        
        status_text.text("Fusing predictions...")
        progress_bar.progress(95)
        fusion_prediction = fusion_model.predict(
            visual_results['features'],
            audio_emotion_results['features'],
            text_results['features']
        )
        
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()
        
        fps = video_info.get('fps', 1)
        duration = video_info.get('duration', len(frames))
        timestamps = [i * (duration / len(visual_results['frame_emotions'])) 
                     for i in range(len(visual_results['frame_emotions']))] if visual_results['frame_emotions'] else None
        
        results['success'] = True
        results['video_path'] = video_path
        results['visual'] = visual_results
        results['audio'] = audio_emotion_results
        results['text'] = text_results
        results['fusion'] = fusion_prediction
        results['transcript'] = audio_results['transcript']
        results['word_emotions'] = word_emotions
        results['frames_count'] = len(frames)
        results['detection_rate'] = visual_results['detection_rate']
        results['timestamps'] = timestamps
        results['duration'] = duration
        results['video_info'] = video_info
        return results
    except Exception as e:
        results['error'] = f"Error: {str(e)}"
        import traceback
        print(traceback.format_exc())
        return results

def process_audio_only(audio_path, audio_encoder, text_encoder, audio_processor, visualizer, word_analyzer):
    results = {'success': False, 'error': None, 'mode': 'audio'}
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Transcribing audio...")
        progress_bar.progress(30)
        transcript_result = audio_processor.transcribe_audio(audio_path)
        
        status_text.text("Analyzing voice emotion...")
        progress_bar.progress(50)
        audio_emotion_results = audio_encoder.analyze_audio(audio_path)
        
        status_text.text("Analyzing text emotion...")
        progress_bar.progress(70)
        text_content = transcript_result['text'] if transcript_result['text'] else "No speech detected"
        text_results = text_encoder.analyze_text(text_content)
        
        status_text.text("Analyzing word-level emotions...")
        progress_bar.progress(85)
        word_emotions = word_analyzer.highlight_transcript(text_content) if text_content != "No speech detected" else []
        
        status_text.text("Combining audio and text...")
        progress_bar.progress(95)
        
        audio_7 = audio_emotion_results['audio_emotions_7']
        text_em = text_results['text_emotions']
        
        combined = {}
        for emotion in config.EMOTION_LABELS:
            combined[emotion] = audio_7.get(emotion, 0) * 0.4 + text_em.get(emotion, 0) * 0.6
        
        predicted_emotion = max(combined.items(), key=lambda x: x[1])[0]
        confidence = combined[predicted_emotion]
        
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()
        
        results['success'] = True
        results['audio_path'] = audio_path
        results['audio'] = audio_emotion_results
        results['text'] = text_results
        results['combined'] = {
            'predicted_emotion': predicted_emotion,
            'confidence': confidence,
            'probabilities': combined
        }
        results['transcript'] = transcript_result
        results['word_emotions'] = word_emotions
        return results
    except Exception as e:
        results['error'] = f"Error: {str(e)}"
        import traceback
        print(traceback.format_exc())
        return results

def display_word_highlighting_compact(word_emotions):
    if not word_emotions:
        return
    
    st.markdown("**Word-Level Emotions**")
    
    html_parts = []
    for word_data in word_emotions:
        phrase = word_data['phrase']
        emotion = word_data['emotion']
        confidence = word_data['confidence']
        color = config.COLOR_SCHEME.get(emotion, '#CCCCCC')
        
        html_parts.append(
            f'<span style="background-color: {color}; padding: 2px 5px; margin: 1px; '
            f'border-radius: 3px; display: inline-block; color: white; font-size: 0.85em;" '
            f'title="{emotion.capitalize()}: {confidence:.1%}">{phrase}</span>'
        )
    
    html_content = ' '.join(html_parts)
    st.markdown(f'<div style="line-height: 2; padding: 10px; background-color: #f8f9fa; '
                f'border-radius: 6px; max-height: 200px; overflow-y: auto;">{html_content}</div>', 
                unsafe_allow_html=True)

def display_prediction_summary(predicted_emotion, confidence, visual_emotion, audio_emotion, text_emotion, face_detection):
    emotion_color = config.COLOR_SCHEME.get(predicted_emotion, '#CCCCCC')
    
    st.markdown("**Emotion Analysis**")
    
    html = f"""
    <div style="background: linear-gradient(135deg, {emotion_color} 0%, {emotion_color}dd 100%); 
                padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">
        <div style="font-size: 2em; font-weight: bold; text-align: center; margin-bottom: 10px;">
            {predicted_emotion.upper()}
        </div>
        <div style="text-align: center; font-size: 1.2em; margin-bottom: 15px;">
            Confidence: {confidence:.1%}
        </div>
        <div style="background-color: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
            <div style="font-weight: 600; margin-bottom: 10px;">Individual Modalities:</div>
            <div style="margin: 5px 0;">📺 Visual: <span style="background-color: {config.COLOR_SCHEME.get(visual_emotion, '#666')}; 
                padding: 3px 10px; border-radius: 4px; font-weight: 600;">{visual_emotion}</span></div>
            <div style="margin: 5px 0;">↻ ◁ || ▷ ↺ Audio: <span style="background-color: {config.COLOR_SCHEME.get(audio_emotion, '#666')}; 
                padding: 3px 10px; border-radius: 4px; font-weight: 600;">{audio_emotion}</span></div>
            <div style="margin: 5px 0;">📜 Text: <span style="background-color: {config.COLOR_SCHEME.get(text_emotion, '#666')}; 
                padding: 3px 10px; border-radius: 4px; font-weight: 600;">{text_emotion}</span></div>
            <div style="margin: 10px 0 5px 0; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3);">
                Face Detection: {face_detection:.0%}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def display_audio_prediction_summary(predicted_emotion, confidence, audio_emotion, text_emotion):
    emotion_color = config.COLOR_SCHEME.get(predicted_emotion, '#CCCCCC')
    
    st.markdown("**Emotion Analysis**")
    
    html = f"""
    <div style="background: linear-gradient(135deg, {emotion_color} 0%, {emotion_color}dd 100%); 
                padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">
        <div style="font-size: 2em; font-weight: bold; text-align: center; margin-bottom: 10px;">
            {predicted_emotion.upper()}
        </div>
        <div style="text-align: center; font-size: 1.2em; margin-bottom: 15px;">
            Confidence: {confidence:.1%}
        </div>
        <div style="background-color: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
            <div style="font-weight: 600; margin-bottom: 10px;">Individual Modalities:</div>
            <div style="margin: 5px 0;">↻ ◁ || ▷ ↺ Audio (Voice Tone): <span style="background-color: {config.COLOR_SCHEME.get(audio_emotion, '#666')}; 
                padding: 3px 10px; border-radius: 4px; font-weight: 600;">{audio_emotion}</span></div>
            <div style="margin: 5px 0;">📜 Text (Speech Content): <span style="background-color: {config.COLOR_SCHEME.get(text_emotion, '#666')}; 
                padding: 3px 10px; border-radius: 4px; font-weight: 600;">{text_emotion}</span></div>
            <div style="margin: 10px 0 5px 0; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3); font-size: 0.9em;">
                Weighted: Audio 40% + Text 60%
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def generate_pdf_bytes(results, mode="video"):
    """Generate PDF and return bytes"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"emosense_report_{mode}_{timestamp}.pdf"
        pdf_path = config.TEMP_DIR / pdf_filename
        
        if mode == "video":
            generate_video_report(results, str(pdf_path))
        else:
            generate_audio_report(results, str(pdf_path))
        
        with open(pdf_path, "rb") as pdf_file:
            return pdf_file.read(), pdf_filename
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None, None

def display_advanced_metrics(metrics, visualizer):
    """Display advanced metrics section"""
    # Check if user has access to advanced metrics
    limits = get_user_limits()
    
    if not limits['advanced_metrics']:
        st.markdown("---")
        st.header("👩🏻‍💻 Advanced Candidate Performance Metrics")
        st.warning("⭐ Advanced metrics are available in Premium plan")
        st.info("Upgrade to Premium to unlock:")
        st.markdown("""
        - **Performance Breakdown** - Radar chart with 6 key metrics
        - **Individual Gauges** - Detailed scores for each metric
        - **Personalized Recommendations** - AI-powered suggestions
        """)
        if st.button("💎 Upgrade to Premium"):
            st.session_state.page = "💎 Subscription"
            st.rerun()
        return
    
    st.markdown("---")
    st.header("👩🏻‍💻 Advanced Candidate Performance Metrics")

    # Overall score
    overall_score = metrics['overall']
    overall_color = '#2ECC71' if overall_score >= 75 else '#F39C12' if overall_score >= 50 else '#E74C3C'
    
    st.markdown(f"""
    <div style="background: {overall_color}; padding: 20px; border-radius: 10px; color: white; margin: 10px 0; text-align: center;">
        <div style="font-size: 1.5em; font-weight: bold;">Overall Performance Score</div>
        <div style="font-size: 3em; font-weight: bold;">{overall_score:.0f}/100</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Radar chart
    st.subheader("Performance Breakdown")
    radar_fig = visualizer.create_advanced_metrics_chart(metrics)
    st.plotly_chart(radar_fig, use_container_width=True)
    
    # Individual metrics gauges
    st.subheader("Individual Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gauge1 = visualizer.create_metric_gauge(metrics['engagement'], "Engagement")
        st.plotly_chart(gauge1, use_container_width=True)
        
        gauge2 = visualizer.create_metric_gauge(metrics['communication'], "Communication")
        st.plotly_chart(gauge2, use_container_width=True)
    
    with col2:
        gauge3 = visualizer.create_metric_gauge(metrics['confidence'], "Confidence")
        st.plotly_chart(gauge3, use_container_width=True)
        
        gauge4 = visualizer.create_metric_gauge(metrics['positivity'], "Positivity")
        st.plotly_chart(gauge4, use_container_width=True)
    
    with col3:
        gauge5 = visualizer.create_metric_gauge(100 - metrics['stress'], "Calm (Low Stress)")
        st.plotly_chart(gauge5, use_container_width=True)
        
        gauge6 = visualizer.create_metric_gauge(metrics['stability'], "Emotional Stability")
        st.plotly_chart(gauge6, use_container_width=True)
    
    # Recommendations
    if metrics.get('recommendations'):
        st.markdown("---")
        st.subheader("Personalized Emotion Improvement Recommendations")
        
        for rec in metrics['recommendations']:
            with st.expander(f"{rec['category']}: {rec['issue']}"):
                st.info(rec['suggestion'])

def display_video_results(results, visualizer, metrics_calc):
    if not results['success']:
        st.error(results['error'])
        return
    
    # Calculate advanced metrics
    metrics = metrics_calc.calculate_all_metrics(results)
    
    # Check history limit before saving
    if not check_history_limit():
        st.warning("Sorry, You've reached the free plan limit of 10 saved analyses")
        show_upgrade_prompt('history')
    else:
        # Save to history
        file_name = Path(results['video_path']).name
        file_size = Path(results['video_path']).stat().st_size / (1024 * 1024)  # MB
        save_analysis(
            st.session_state.user['id'],
            'video',
            file_name,
            results,
            metrics,
            file_size=file_size,
            duration=results.get('duration', 0)
        )
    
    st.markdown("---")
    st.header("Analysis Results")
    
    # Generate PDF immediately
    with st.spinner("Generating PDF report..."):
        pdf_bytes, pdf_filename = generate_pdf_bytes(results, mode="video")
    
    if pdf_bytes:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                type="primary"
            )
        
        with col2:
            # Generate CSV
            csv_path = export_to_csv(results, metrics)
            csv_bytes = get_export_bytes(csv_path)
            st.download_button(
                label="📊 Export CSV",
                data=csv_bytes,
                file_name=csv_path.name,
                mime="text/csv"
            )
        
        with col3:
            # Generate JSON
            json_path = export_to_json(results, metrics)
            json_bytes = get_export_bytes(json_path)
            st.download_button(
                label="💾 Export JSON",
                data=json_bytes,
                file_name=json_path.name,
                mime="application/json"
            )
    
    st.markdown("---")
    st.subheader("Video & Analysis")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.video(results['video_path'])
        video_info = results.get('video_info', {})
        st.caption(f"Duration: {results.get('duration', 0):.1f}s | "
                  f"FPS: {video_info.get('fps', 0):.1f} | "
                  f"Frames: {results['frames_count']}")
    
    with col2:
        st.markdown("**Transcript**")
        st.text_area("Transcript", value=results['transcript']['text'] if results['transcript']['text'] else "No speech detected", 
                    height=150, label_visibility="collapsed")
        
        if results.get('word_emotions') and len(results['word_emotions']) > 0:
            st.markdown("")
            display_word_highlighting_compact(results['word_emotions'])
        
        st.markdown("")
        predicted_emotion = results['fusion']['predicted_emotion']
        confidence = results['fusion']['confidence']
        display_prediction_summary(
            predicted_emotion,
            confidence,
            results['visual']['dominant_emotion'],
            results['audio']['dominant_emotion'],
            results['text']['dominant_emotion'],
            results['detection_rate']
        )
    
    # Display advanced metrics
    display_advanced_metrics(metrics, visualizer)
    
    if results['visual']['frame_emotions'] and len(results['visual']['frame_emotions']) > 1:
        st.markdown("---")
        st.subheader("Emotion Timeline")
        timeline_fig = visualizer.create_emotion_timeline(
            results['visual']['frame_emotions'],
            timestamps=results.get('timestamps'),
            title="Emotional journey throughout the video"
        )
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        dominant_fig = visualizer.create_dominant_emotion_timeline(
            results['visual']['frame_emotions'],
            timestamps=results.get('timestamps')
        )
        if dominant_fig:
            st.plotly_chart(dominant_fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Overall Emotion Distribution")
    fig = visualizer.create_emotion_bar_chart(results['fusion']['probabilities'])
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Modality Breakdown")
    fusion_weights = results['fusion']['attention_info']['fusion_weights']
    fig = visualizer.create_modality_comparison(
        results['visual']['aggregated_emotions'],
        results['audio'].get('audio_emotions_7', {}),
        results['text']['text_emotions'],
        fusion_weights
    )
    st.plotly_chart(fig, use_container_width=True)

def display_audio_results(results, visualizer, metrics_calc):
    if not results['success']:
        st.error(results['error'])
        return
    
    # Calculate advanced metrics
    metrics = metrics_calc.calculate_all_metrics(results)
    
    # Check history limit before saving
    if not check_history_limit():
        st.warning("Sorry, You've reached the free plan limit of 10 saved analyses")
        show_upgrade_prompt('history')
    else:
        # Save to history
        file_name = Path(results['audio_path']).name
        file_size = Path(results['audio_path']).stat().st_size / (1024 * 1024)  # MB
        save_analysis(
            st.session_state.user['id'],
            'audio',
            file_name,
            results,
            metrics,
            file_size=file_size,
            duration=results.get('duration', 0)
        )
    
    st.markdown("---")
    st.header("Audio Analysis Results")
    
    # Generate PDF immediately
    with st.spinner("Generating PDF report..."):
        pdf_bytes, pdf_filename = generate_pdf_bytes(results, mode="audio")
    
    if pdf_bytes:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                type="primary"
            )
        
        with col2:
            # Generate CSV
            csv_path = export_to_csv(results, metrics)
            csv_bytes = get_export_bytes(csv_path)
            st.download_button(
                label="📊 Export CSV",
                data=csv_bytes,
                file_name=csv_path.name,
                mime="text/csv"
            )
        
        with col3:
            # Generate JSON
            json_path = export_to_json(results, metrics)
            json_bytes = get_export_bytes(json_path)
            st.download_button(
                label="💾 Export JSON",
                data=json_bytes,
                file_name=json_path.name,
                mime="application/json"
            )
    
    st.markdown("---")
    st.subheader("Audio & Analysis")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Audio Recording**")
        st.audio(results['audio_path'])
        st.caption("Listen to your recording")
    
    with col2:
        st.markdown("**Transcript**")
        st.text_area("Transcript", value=results['transcript']['text'] if results['transcript']['text'] else "No speech detected",
                    height=150, label_visibility="collapsed")
        
        if results.get('word_emotions') and len(results['word_emotions']) > 0:
            st.markdown("")
            display_word_highlighting_compact(results['word_emotions'])
        
        st.markdown("")
        predicted_emotion = results['combined']['predicted_emotion']
        confidence = results['combined']['confidence']
        display_audio_prediction_summary(
            predicted_emotion,
            confidence,
            results['audio']['dominant_emotion'],
            results['text']['dominant_emotion']
        )
    
    # Display advanced metrics
    display_advanced_metrics(metrics, visualizer)
    
    st.markdown("---")
    st.subheader("Overall Emotion Distribution")
    fig = visualizer.create_emotion_bar_chart(results['combined']['probabilities'], 
                                               title="Combined Audio + Text Emotion")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Modality Breakdown")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Audio (Voice Tone) - 40% Weight**")
        audio_fig = visualizer.create_emotion_bar_chart(
            results['audio']['audio_emotions_7'],
            title="Audio Emotion Analysis"
        )
        st.plotly_chart(audio_fig, use_container_width=True)
    
    with col2:
        st.markdown("**Text (Speech Content) - 60% Weight**")
        text_fig = visualizer.create_emotion_bar_chart(
            results['text']['text_emotions'],
            title="Text Emotion Analysis"
        )
        st.plotly_chart(text_fig, use_container_width=True)

def main():
    st.title("🎭 EmoSense Interview Analyzer")
    st.markdown("Multimodal emotion recognition with advanced metrics and performance insights")
    
    try:
        fusion_model, visual_encoder, audio_encoder, text_encoder, word_analyzer, metrics_calc = load_models()
        video_processor, audio_processor, visualizer = load_processors()
    except Exception as e:
        st.error(f"Error loading: {e}")
        st.stop()

    tab1, tab2 = st.tabs(["⬆️ Upload", "⏺️ Record"])

    with tab1:
        st.header("Upload Files for Analysis")
        
        upload_type = st.radio("Select file type:", ["Video File", "Audio File"], horizontal=True)
        
        if upload_type == "Video File":
            st.markdown("### Upload Video")
            st.success("🧐 Analyze emotion from facial expressions + voice + speech content")
            
            # Show limits
            limits = get_user_limits()
            st.info(f"📁 {limits['name']} plan: Upload files up to {limits['max_upload_size_mb']} MB")
            
            uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'avi', 'mov', 'mkv'], key="video_upload")
            
            if uploaded_file:
                # Check file size
                file_size_mb = uploaded_file.size / (1024 * 1024)
                
                if not check_upload_limit(file_size_mb):
                    st.error(f"SORRY, File size ({file_size_mb:.1f} MB) exceeds your limit ({limits['max_upload_size_mb']} MB)")
                    show_upgrade_prompt('upload')
                else:
                    video_path = config.TEMP_DIR / uploaded_file.name
                    with open(video_path, 'wb') as f:
                        f.write(uploaded_file.read())
                    
                    is_valid, message, duration = video_processor.validate_video(video_path)
                    if not is_valid:
                        st.error(message)
                    else:
                        st.success(f"✓ Video ready - Duration: {duration:.1f}s, Size: {file_size_mb:.1f} MB")
                        
                        if st.button("🔍 Analyze Video", type="primary"):
                            results = process_video(str(video_path), fusion_model, visual_encoder, audio_encoder, 
                                                   text_encoder, video_processor, audio_processor, visualizer, word_analyzer)
                            display_video_results(results, visualizer, metrics_calc)
        
        else:  # Audio File
            st.markdown("### Upload Audio")
            st.success("🧐 Analyze emotion from voice tone + speech content")

            # Show limits
            limits = get_user_limits()
            st.info(f"📁 {limits['name']} plan: Upload files up to {limits['max_upload_size_mb']} MB")
            
            uploaded_audio = st.file_uploader("Choose an audio file", 
                                             type=['mp3', 'wav', 'm4a', 'ogg', 'aac'], 
                                             key="audio_upload")
            
            if uploaded_audio:
                # Check file size
                file_size_mb = uploaded_audio.size / (1024 * 1024)
                if not check_upload_limit(file_size_mb):
                    st.error(f"SORRY, File size ({file_size_mb:.1f} MB) exceeds your limit ({limits['max_upload_size_mb']} MB)")
                    show_upgrade_prompt('upload')
                else:
                    audio_path = config.TEMP_DIR / uploaded_audio.name
                    with open(audio_path, 'wb') as f:
                        f.write(uploaded_audio.read())
                    
                    st.success(f"✓ Audio uploaded: {uploaded_audio.name} ({file_size_mb:.1f} MB)")
                    st.audio(str(audio_path))
                    
                    if st.button("🔍 Analyze Audio", type="primary"):
                        results = process_audio_only(str(audio_path), audio_encoder, text_encoder, 
                                                    audio_processor, visualizer, word_analyzer)
                        display_audio_results(results, visualizer, metrics_calc)
    
    with tab2:
        st.header("Record for Analysis")
        
        record_type = st.radio("Select recording type:", ["Webcam (Video + Audio)", "Microphone (Audio Only)"], horizontal=True)
        
        if record_type == "Webcam (Video + Audio)":
            st.markdown("### Record from Webcam")
            st.success("🎥 Captures video from webcam + audio from microphone")
            
            # Get user limits
            limits = get_user_limits()
            max_duration = limits['max_recording_duration']
            
            duration = st.slider(
                "Recording duration (seconds)", 
                min_value=config.MIN_RECORDING_DURATION,
                max_value=max_duration,
                value=min(config.DEFAULT_RECORDING_DURATION, max_duration),
                key="webcam_duration"
            )
            
            if limits['name'] == 'Free':
                st.info(f"𝓯𝓻𝓮𝓮 Free plan: Up to {max_duration} seconds")
                st.caption("⭐ Premium: Up to 120 seconds")
            else:
                st.success(f"⭐ Premium: Up to {max_duration} seconds")
            
            if st.button("⏺ Start Webcam Recording", type="primary"):
                output_path = config.TEMP_DIR / "webcam_recording.mp4"
                video_path, error = record_webcam_with_audio(output_path, duration, camera_index=0)
                
                if error:
                    st.error(error)
                else:
                    results = process_video(video_path, fusion_model, visual_encoder, audio_encoder, 
                                           text_encoder, video_processor, audio_processor, visualizer, word_analyzer)
                    display_video_results(results, visualizer, metrics_calc)
        
        else:  # Audio Only
            st.markdown("### Record from Microphone")
            st.success("🎤 Records audio only from your microphone")
            
            # Get user limits
            limits = get_user_limits()
            max_duration = limits['max_recording_duration']
            
            duration = st.slider(
                "Recording duration (seconds)",
                min_value=config.MIN_RECORDING_DURATION,
                max_value=max_duration,
                value=min(config.DEFAULT_RECORDING_DURATION, max_duration),
                key="audio_duration"
            )
            
            if limits['name'] == 'Free':
                st.info(f"𝓯𝓻𝓮𝓮 Free plan: Up to {max_duration} seconds")
                st.caption("⭐ Premium: Up to 120 seconds")
            else:
                st.success(f"⭐ Premium: Up to {max_duration} seconds")
            
            if st.button("⏺ Start Audio Recording", type="primary"):
                output_path = config.TEMP_DIR / "mic_recording.m4a"
                audio_path, error = record_audio_from_mic(output_path, duration)
                
                if error:
                    st.error(error)
                else:
                    results = process_audio_only(audio_path, audio_encoder, text_encoder, 
                                                audio_processor, visualizer, word_analyzer)
                    display_audio_results(results, visualizer, metrics_calc)

if __name__ == "__main__":
    main()
