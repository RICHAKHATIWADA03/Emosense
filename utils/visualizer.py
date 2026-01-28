"""Emotion Visualization Utilities - With Timeline"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
import config

class EmotionVisualizer:
    def __init__(self):
        self.colors = config.COLOR_SCHEME
    
    def create_emotion_bar_chart(self, emotions, title="Emotion Distribution"):
        sorted_emotions = dict(sorted(emotions.items(), key=lambda x: x[1], reverse=True))
        emotions_list = list(sorted_emotions.keys())
        probabilities = list(sorted_emotions.values())
        colors_list = [self.colors.get(e, '#CCCCCC') for e in emotions_list]
        
        fig = go.Figure(data=[go.Bar(
            x=emotions_list, y=probabilities, marker_color=colors_list,
            text=[f"{p:.1%}" for p in probabilities], textposition='auto'
        )])
        fig.update_layout(
            title=title, xaxis_title="Emotion", yaxis_title="Probability",
            yaxis=dict(range=[0, 1], tickformat='.0%'), height=400,
            showlegend=False, template='plotly_white'
        )
        return fig
    
    def create_emotion_timeline(self, frame_emotions, timestamps=None, title="Emotion Timeline"):
        """Create a timeline showing emotion changes over time"""
        if not frame_emotions or len(frame_emotions) == 0:
            return None
        
        # If timestamps not provided, create them based on frame count
        if timestamps is None:
            timestamps = list(range(len(frame_emotions)))
        
        # Extract emotions for each frame
        emotion_traces = {emotion: [] for emotion in config.EMOTION_LABELS}
        
        for frame_emotion in frame_emotions:
            for emotion in config.EMOTION_LABELS:
                emotion_traces[emotion].append(frame_emotion.get(emotion, 0))
        
        # Create figure
        fig = go.Figure()
        
        # Add a line for each emotion
        for emotion in config.EMOTION_LABELS:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=emotion_traces[emotion],
                mode='lines+markers',
                name=emotion.capitalize(),
                line=dict(color=self.colors.get(emotion, '#CCCCCC'), width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (seconds)" if timestamps != list(range(len(frame_emotions))) else "Frame",
            yaxis_title="Emotion Probability",
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            height=500,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    def create_modality_comparison(self, visual_emotions, audio_emotions, text_emotions, fusion_weights=None):
        emotions = list(config.EMOTION_LABELS)
        fig = go.Figure()
        
        weight_v = f" (weight: {fusion_weights['visual']:.1f})" if fusion_weights else ""
        fig.add_trace(go.Bar(name=f'Visual{weight_v}', x=emotions,
            y=[visual_emotions.get(e, 0) for e in emotions], marker_color='rgba(75, 192, 192, 0.7)'))
        
        weight_a = f" (weight: {fusion_weights['audio']:.1f})" if fusion_weights else ""
        fig.add_trace(go.Bar(name=f'Audio{weight_a}', x=emotions,
            y=[audio_emotions.get(e, 0) for e in emotions], marker_color='rgba(255, 159, 64, 0.7)'))
        
        weight_t = f" (weight: {fusion_weights['text']:.1f})" if fusion_weights else ""
        fig.add_trace(go.Bar(name=f'Text{weight_t}', x=emotions,
            y=[text_emotions.get(e, 0) for e in emotions], marker_color='rgba(153, 102, 255, 0.7)'))
        
        fig.update_layout(
            title="Modality Contribution Breakdown", xaxis_title="Emotion",
            yaxis_title="Probability", yaxis=dict(range=[0, 1], tickformat='.0%'),
            barmode='group', height=500, template='plotly_white'
        )
        return fig
    
    def create_dominant_emotion_timeline(self, frame_emotions, timestamps=None):
        """Shows which emotion was dominant at each point in time"""
        if not frame_emotions or len(frame_emotions) == 0:
            return None
        
        if timestamps is None:
            timestamps = list(range(len(frame_emotions)))
        
        # Get dominant emotion for each frame
        dominant_emotions = []
        for frame_emotion in frame_emotions:
            dominant = max(frame_emotion.items(), key=lambda x: x[1])[0]
            dominant_emotions.append(dominant)
        
        # Map emotions to numeric values for visualization
        emotion_to_num = {emotion: i for i, emotion in enumerate(config.EMOTION_LABELS)}
        emotion_values = [emotion_to_num[e] for e in dominant_emotions]
        
        # Create colored segments
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=emotion_values,
            mode='lines+markers',
            line=dict(color='lightgray', width=1),
            marker=dict(
                size=12,
                color=emotion_values,
                colorscale=[[i/(len(config.EMOTION_LABELS)-1), self.colors.get(emotion, '#CCCCCC')] 
                           for i, emotion in enumerate(config.EMOTION_LABELS)],
                showscale=False
            ),
            text=dominant_emotions,
            hovertemplate='<b>%{text}</b><br>Time: %{x}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Dominant Emotion Over Time",
            xaxis_title="Time (seconds)" if timestamps != list(range(len(frame_emotions))) else "Frame",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(config.EMOTION_LABELS))),
                ticktext=[e.capitalize() for e in config.EMOTION_LABELS]
            ),
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    def create_interview_metrics(self, emotions, transcript=""):
        confidence_score = emotions.get('happy', 0) + emotions.get('surprise', 0) * 0.5
        confidence_level = "High" if confidence_score >= config.CONFIDENCE_THRESHOLD else "Medium" if confidence_score >= 0.4 else "Low"
        confidence_color = "green" if confidence_score >= config.CONFIDENCE_THRESHOLD else "orange" if confidence_score >= 0.4 else "red"
        
        nervousness_score = emotions.get('fear', 0) + emotions.get('sad', 0) * 0.7
        nervousness_level = "High" if nervousness_score >= config.NERVOUSNESS_THRESHOLD else "Moderate" if nervousness_score >= 0.3 else "Low"
        nervousness_color = "red" if nervousness_score >= config.NERVOUSNESS_THRESHOLD else "orange" if nervousness_score >= 0.3 else "green"
        
        engagement_score = 1.0 - emotions.get('neutral', 0)
        engagement_level = "High" if engagement_score >= config.ENGAGEMENT_THRESHOLD else "Moderate" if engagement_score >= 0.3 else "Low"
        engagement_color = "green" if engagement_score >= config.ENGAGEMENT_THRESHOLD else "orange" if engagement_score >= 0.3 else "red"
        
        enthusiasm_score = emotions.get('happy', 0) + emotions.get('surprise', 0)
        enthusiasm_level = "High" if enthusiasm_score > 0.5 else "Moderate" if enthusiasm_score > 0.25 else "Low"
        
        return {
            'confidence': {'score': confidence_score, 'level': confidence_level, 'color': confidence_color,
                          'description': "Confidence and self-assurance"},
            'nervousness': {'score': nervousness_score, 'level': nervousness_level, 'color': nervousness_color,
                           'description': "Signs of nervousness or anxiety"},
            'engagement': {'score': engagement_score, 'level': engagement_level, 'color': engagement_color,
                          'description': "Overall engagement"},
            'enthusiasm': {'score': enthusiasm_score, 'level': enthusiasm_level,
                          'description': "Enthusiasm and excitement"}
        }

    def create_advanced_metrics_chart(self, metrics):
        """Create radar chart for advanced metrics"""
        categories = ['Engagement', 'Confidence', 'Communication', 
                     'Positivity', 'Stability', 'Low Stress']
        
        values = [
            metrics['engagement'],
            metrics['confidence'],
            metrics['communication'],
            metrics['positivity'],
            metrics['stability'],
            100 - metrics['stress']  # Invert stress (lower is better)
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Your Score',
            line=dict(color='#3498DB', width=2),
            fillcolor='rgba(52, 152, 219, 0.3)'
        ))
        
        # Add ideal/target line
        fig.add_trace(go.Scatterpolar(
            r=[75] * len(categories),
            theta=categories,
            fill='toself',
            name='Target',
            line=dict(color='#2ECC71', width=1, dash='dash'),
            fillcolor='rgba(46, 204, 113, 0.1)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Performance Metrics",
            height=500
        )
        
        return fig
    
    def create_metric_gauge(self, score, title):
        """Create gauge chart for a single metric"""
        from utils.advanced_metrics import AdvancedMetricsCalculator
        calc = AdvancedMetricsCalculator()
        color = calc.get_metric_color(score)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 16}},
            delta={'reference': 75},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': '#FFEBEE'},
                    {'range': [40, 75], 'color': '#FFF9C4'},
                    {'range': [75, 100], 'color': '#E8F5E9'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        
        fig.update_layout(height=250)
        return fig
