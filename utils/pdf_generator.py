"""Generate PDF reports for emotion analysis"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import plotly.graph_objects as go
from pathlib import Path
import config
import io
from PIL import Image as PILImage

class EmotionReportGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.doc = SimpleDocTemplate(output_path, pagesize=letter,
                                     rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
    def add_title(self, title="EmoSense Emotion Analysis Report"):
        """Add report title"""
        self.story.append(Paragraph(title, self.title_style))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.story.append(Paragraph(f"<i>Generated: {timestamp}</i>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_summary(self, predicted_emotion, confidence, mode="video"):
        """Add analysis summary"""
        self.story.append(Paragraph("Analysis Summary", self.heading_style))
        
        # Create summary table
        data = [
            ['Analysis Type', mode.upper()],
            ['Predicted Emotion', predicted_emotion.upper()],
            ['Confidence', f'{confidence:.1%}'],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_modality_breakdown(self, visual_emotion, audio_emotion, text_emotion, 
                               visual_conf, audio_conf, text_conf):
        """Add modality breakdown"""
        self.story.append(Paragraph("Modality Breakdown", self.heading_style))
        
        data = [
            ['Modality', 'Emotion', 'Confidence'],
            ['Visual (Facial)', visual_emotion.capitalize(), f'{visual_conf:.1%}'],
            ['Audio (Voice)', audio_emotion.capitalize(), f'{audio_conf:.1%}'],
            ['Text (Speech)', text_emotion.capitalize(), f'{text_conf:.1%}']
        ]
        
        table = Table(data, colWidths=[2*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_transcript(self, transcript_text):
        """Add transcript"""
        self.story.append(Paragraph("Transcript", self.heading_style))
        
        if transcript_text and transcript_text != "No speech detected":
            # Wrap text
            para = Paragraph(transcript_text, self.styles['Normal'])
            self.story.append(para)
        else:
            self.story.append(Paragraph("<i>No speech detected</i>", self.styles['Normal']))
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_emotion_distribution(self, probabilities):
        """Add emotion distribution table"""
        self.story.append(Paragraph("Emotion Probabilities", self.heading_style))
        
        # Sort by probability
        sorted_emotions = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        
        data = [['Emotion', 'Probability', 'Bar']]
        for emotion, prob in sorted_emotions:
            bar_width = int(prob * 20)  # Scale to 20 chars max
            bar = '█' * bar_width
            data.append([emotion.capitalize(), f'{prob:.1%}', bar])
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_video_metadata(self, duration, fps, frames_count, detection_rate):
        """Add video metadata"""
        self.story.append(Paragraph("Video Information", self.heading_style))
        
        data = [
            ['Duration', f'{duration:.1f} seconds'],
            ['Frame Rate', f'{fps:.1f} FPS'],
            ['Frames Analyzed', str(frames_count)],
            ['Face Detection Rate', f'{detection_rate:.0%}']
        ]
        
        table = Table(data, colWidths=[2.5*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_word_emotions(self, word_emotions):
        """Add word-level emotion highlights"""
        if not word_emotions or len(word_emotions) == 0:
            return
        
        self.story.append(Paragraph("Word-Level Emotion Analysis", self.heading_style))
        
        # Group by emotion
        emotion_groups = {}
        for item in word_emotions:
            emotion = item['emotion']
            if emotion not in emotion_groups:
                emotion_groups[emotion] = []
            emotion_groups[emotion].append(item['phrase'])
        
        for emotion, phrases in emotion_groups.items():
            color = config.COLOR_SCHEME.get(emotion, '#CCCCCC')
            emotion_text = f"<b>{emotion.upper()}</b>: {', '.join(phrases[:10])}"  # Limit to 10 phrases
            self.story.append(Paragraph(emotion_text, self.styles['Normal']))
            self.story.append(Spacer(1, 0.1*inch))
        
        self.story.append(Spacer(1, 0.2*inch))
    
    def build(self):
        """Build the PDF"""
        self.doc.build(self.story)
        return self.output_path


def generate_video_report(results, output_path):
    """Generate PDF report for video analysis"""
    try:
        generator = EmotionReportGenerator(output_path)
        
        # Add sections
        generator.add_title("EmoSense Video Emotion Analysis Report")
        
        generator.add_summary(
            results['fusion']['predicted_emotion'],
            results['fusion']['confidence'],
            mode="video"
        )
        
        # Get individual emotion confidences - safely
        visual_probs = results['visual'].get('aggregated_emotions', {})
        audio_probs = results['audio'].get('audio_emotions_7', {})
        text_probs = results['text'].get('text_emotions', {})
        
        visual_emotion = results['visual'].get('dominant_emotion', 'neutral')
        audio_emotion = results['audio'].get('dominant_emotion', 'neutral')
        text_emotion = results['text'].get('dominant_emotion', 'neutral')
        
        # Get confidences safely
        visual_conf = visual_probs.get(visual_emotion, 0.0)
        audio_conf = audio_probs.get(audio_emotion, 0.0)
        text_conf = text_probs.get(text_emotion, 0.0)
        
        generator.add_modality_breakdown(
            visual_emotion, audio_emotion, text_emotion,
            visual_conf, audio_conf, text_conf
        )
        
        generator.add_emotion_distribution(results['fusion']['probabilities'])
        
        generator.add_video_metadata(
            results.get('duration', 0),
            results.get('video_info', {}).get('fps', 30),
            results.get('frames_count', 0),
            results.get('detection_rate', 0)
        )
        
        generator.add_transcript(results.get('transcript', {}).get('text', ''))
        
        generator.add_word_emotions(results.get('word_emotions', []))
        
        return generator.build()
    except Exception as e:
        print(f"Error generating video report: {e}")
        import traceback
        traceback.print_exc()
        raise


def generate_audio_report(results, output_path):
    """Generate PDF report for audio analysis"""
    try:
        generator = EmotionReportGenerator(output_path)
        
        generator.add_title("EmoSense Audio Emotion Analysis Report")
        
        generator.add_summary(
            results['combined']['predicted_emotion'],
            results['combined']['confidence'],
            mode="audio"
        )
        
        # Get individual confidences safely
        audio_emotion = results['audio'].get('dominant_emotion', 'neutral')
        text_emotion = results['text'].get('dominant_emotion', 'neutral')
        
        audio_probs = results['audio'].get('audio_emotions_7', {})
        text_probs = results['text'].get('text_emotions', {})
        
        audio_conf = audio_probs.get(audio_emotion, 0.0)
        text_conf = text_probs.get(text_emotion, 0.0)
        
        # Add modality breakdown (no visual)
        generator.story.append(Paragraph("Modality Breakdown", generator.heading_style))
        
        data = [
            ['Modality', 'Emotion', 'Confidence', 'Weight'],
            ['Audio (Voice)', audio_emotion.capitalize(), f"{audio_conf:.1%}", '40%'],
            ['Text (Speech)', text_emotion.capitalize(), f"{text_conf:.1%}", '60%']
        ]
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        generator.story.append(table)
        generator.story.append(Spacer(1, 0.3*inch))
        
        generator.add_emotion_distribution(results['combined']['probabilities'])
        
        generator.add_transcript(results.get('transcript', {}).get('text', ''))
        
        generator.add_word_emotions(results.get('word_emotions', []))
        
        return generator.build()
    except Exception as e:
        print(f"Error generating audio report: {e}")
        import traceback
        traceback.print_exc()
        raise
