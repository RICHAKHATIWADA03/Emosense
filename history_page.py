"""Analysis history page"""
import streamlit as st
from database import get_user_history, get_analysis_by_id, delete_analysis, get_user_stats
from utils import EmotionVisualizer, export_to_json, export_to_csv, get_export_bytes
import config

def show_history_page():
    """Display analysis history page"""
    st.title("📊 Analysis History")
    
    user_id = st.session_state.user['id']
    
    # Show user stats
    stats = get_user_stats(user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Analyses", stats['total_analyses'])
    
    with col2:
        st.metric("Average Confidence", f"{stats['average_confidence']:.1%}")
    
    with col3:
        if stats['emotion_distribution']:
            most_common = max(stats['emotion_distribution'].items(), key=lambda x: x[1])
            st.metric("Most Common Emotion", most_common[0].capitalize())
    
    st.markdown("---")
    
    # Get history
    history = get_user_history(user_id, limit=50)
    
    if not history:
        st.info("No analysis history yet. Start analyzing videos or audio!")
        return
    
    # Display history
    st.subheader("Recent Analyses")
    
    for item in history:
        with st.expander(f"{item['file_name'] or 'Recording'} - {item['emotion'].upper()} ({item['date']})"):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(f"**Type:** {item['type'].upper()}")
                st.write(f"**Emotion:** {item['emotion'].capitalize()}")
            
            with col2:
                st.write(f"**Confidence:** {item['confidence']:.1%}")
                st.write(f"**Date:** {item['date']}")
            
            with col3:
                if item['metrics']:
                    st.write(f"**Overall Score:** {item['metrics'].get('overall', 0):.0f}/100")
                    st.write(f"**Stress Level:** {item['metrics'].get('stress', 0):.0f}/100")
            
            with col4:
                # ADD PLAYBACK BUTTON
                if item.get('file_path'):
                    if st.button("▶️ Play", key=f"play_{item['id']}"):
                        st.session_state[f'show_playback_{item["id"]}'] = not st.session_state.get(f'show_playback_{item["id"]}', False)
                
                if st.button("View", key=f"view_{item['id']}"):
                    st.session_state.view_analysis_id = item['id']
                
                if st.button("Delete", key=f"del_{item['id']}"):
                    if delete_analysis(item['id'], user_id):
                        st.success("Deleted!")
                        st.rerun()
            
            # ADD PLAYBACK DISPLAY (SMALL SIZE)
            if st.session_state.get(f'show_playback_{item["id"]}', False):
                st.markdown("---")
                if item.get('file_path'):
                    file_path = item['file_path']
                    # Display in smaller container (webcam size)
                    col_left, col_center, col_right = st.columns([1, 2, 1])
                    with col_center:
                        if item['type'] == 'video' or file_path.endswith(('.mp4', '.avi', '.mov', '.webm')):
                            st.video(file_path)
                        elif item['type'] == 'audio' or file_path.endswith(('.mp3', '.wav', '.m4a')):
                            st.audio(file_path)
                else:
                    st.warning("Original file not available for playback")
    
    # View detailed analysis if selected
    if 'view_analysis_id' in st.session_state and st.session_state.view_analysis_id:
        show_detailed_analysis(st.session_state.view_analysis_id, user_id)

def show_detailed_analysis(analysis_id, user_id):
    """Show detailed analysis view"""
    st.markdown("---")
    st.subheader("Detailed Analysis")
    
    data = get_analysis_by_id(analysis_id, user_id)
    
    if not data:
        st.error("Analysis not found")
        return
    
    results = data['results']
    metrics = data['metrics']
    
    # Show emotion summary
    if 'fusion' in results:
        predicted = results['fusion']['predicted_emotion']
        confidence = results['fusion']['confidence']
        probs = results['fusion']['probabilities']
    else:
        predicted = results['combined']['predicted_emotion']
        confidence = results['combined']['confidence']
        probs = results['combined']['probabilities']
    
    emotion_color = config.COLOR_SCHEME.get(predicted, '#CCCCCC')
    
    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Export to CSV", key=f"export_csv_{analysis_id}"):
            csv_path = export_to_csv(results, metrics)
            csv_bytes = get_export_bytes(csv_path)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_bytes,
                file_name=csv_path.name,
                mime="text/csv",
                key=f"dl_csv_{analysis_id}"
            )
    
    with col2:
        if st.button("💾 Export to JSON", key=f"export_json_{analysis_id}"):
            json_path = export_to_json(results, metrics)
            json_bytes = get_export_bytes(json_path)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_bytes,
                file_name=json_path.name,
                mime="application/json",
                key=f"dl_json_{analysis_id}"
            )
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {emotion_color} 0%, {emotion_color}dd 100%); 
                padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">
        <div style="font-size: 2em; font-weight: bold; text-align: center;">
            {predicted.upper()}
        </div>
        <div style="text-align: center; font-size: 1.2em;">
            Confidence: {confidence:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show transcript
    if results.get('transcript', {}).get('text'):
        st.markdown("**Transcript:**")
        st.text_area("", results['transcript']['text'], height=100, label_visibility="collapsed")
    
    # Show metrics if available
    if metrics:
        st.markdown("---")
        st.subheader("Performance Metrics")
        
        visualizer = EmotionVisualizer()
        
        # Radar chart
        radar_fig = visualizer.create_advanced_metrics_chart(metrics)
        st.plotly_chart(radar_fig, use_container_width=True)
        
        # Individual gauges
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gauge1 = visualizer.create_metric_gauge(metrics['engagement'], "Engagement")
            st.plotly_chart(gauge1, use_container_width=True)
        
        with col2:
            gauge2 = visualizer.create_metric_gauge(metrics['confidence'], "Confidence")
            st.plotly_chart(gauge2, use_container_width=True)
        
        with col3:
            gauge3 = visualizer.create_metric_gauge(100 - metrics['stress'], "Calm")
            st.plotly_chart(gauge3, use_container_width=True)
        
        # Recommendations
        if metrics.get('recommendations'):
            st.markdown("---")
            st.subheader("📝 Recommendations")
            for rec in metrics['recommendations']:
                st.markdown(f"**{rec['category']}:** {rec['issue']}")
                st.info(rec['suggestion'])
    
    if st.button("Close Details"):
        del st.session_state.view_analysis_id
        st.rerun()
