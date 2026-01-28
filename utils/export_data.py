"""Export analysis data to CSV and JSON formats"""
import json
import csv
from pathlib import Path
from datetime import datetime
import config

def export_to_json(results, metrics, output_path=None):
    """Export analysis results to JSON"""
    
    # Prepare data for JSON
    if 'fusion' in results:
        # Video analysis
        export_data = {
            'analysis_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'analysis_type': 'video',
            'timestamp': datetime.now().isoformat(),
            'predicted_emotion': results['fusion']['predicted_emotion'],
            'confidence': float(results['fusion']['confidence']),
            'duration': results.get('duration', 0),
            'transcript': results.get('transcript', {}).get('text', ''),
            'modalities': {
                'visual': {
                    'emotion': results['visual']['dominant_emotion'],
                    'confidence': float(max(results['visual']['aggregated_emotions'].values())),
                    'detection_rate': float(results.get('detection_rate', 0))
                },
                'audio': {
                    'emotion': results['audio']['dominant_emotion'],
                    'confidence': float(max(results['audio']['audio_emotions_7'].values()))
                },
                'text': {
                    'emotion': results['text']['dominant_emotion'],
                    'confidence': float(max(results['text']['text_emotions'].values()))
                }
            },
            'emotion_probabilities': {k: float(v) for k, v in results['fusion']['probabilities'].items()},
            'frame_emotions': results['visual'].get('frame_emotions', []),
            'word_emotions': results.get('word_emotions', []),
            'metrics': {
                'overall': float(metrics['overall']),
                'engagement': float(metrics['engagement']),
                'confidence': float(metrics['confidence']),
                'communication': float(metrics['communication']),
                'positivity': float(metrics['positivity']),
                'stress': float(metrics['stress']),
                'stability': float(metrics['stability'])
            },
            'recommendations': metrics.get('recommendations', [])
        }
    else:
        # Audio analysis
        export_data = {
            'analysis_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'analysis_type': 'audio',
            'timestamp': datetime.now().isoformat(),
            'predicted_emotion': results['combined']['predicted_emotion'],
            'confidence': float(results['combined']['confidence']),
            'transcript': results.get('transcript', {}).get('text', ''),
            'modalities': {
                'audio': {
                    'emotion': results['audio']['dominant_emotion'],
                    'confidence': float(max(results['audio']['audio_emotions_7'].values()))
                },
                'text': {
                    'emotion': results['text']['dominant_emotion'],
                    'confidence': float(max(results['text']['text_emotions'].values()))
                }
            },
            'emotion_probabilities': {k: float(v) for k, v in results['combined']['probabilities'].items()},
            'word_emotions': results.get('word_emotions', []),
            'metrics': {
                'overall': float(metrics['overall']),
                'engagement': float(metrics['engagement']),
                'confidence': float(metrics['confidence']),
                'communication': float(metrics['communication']),
                'positivity': float(metrics['positivity']),
                'stress': float(metrics['stress']),
                'stability': float(metrics['stability'])
            },
            'recommendations': metrics.get('recommendations', [])
        }
    
    # Generate filename if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = config.TEMP_DIR / f"emosense_export_{timestamp}.json"
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return output_path

def export_to_csv(results, metrics, output_path=None):
    """Export analysis results to CSV"""
    
    # Generate filename if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = config.TEMP_DIR / f"emosense_export_{timestamp}.csv"
    
    # Determine if video or audio
    is_video = 'fusion' in results
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['EmoSense Analysis Export'])
        writer.writerow(['Generated:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(['Type:', 'Video' if is_video else 'Audio'])
        writer.writerow([])
        
        # Overall Results
        writer.writerow(['OVERALL RESULTS'])
        if is_video:
            writer.writerow(['Predicted Emotion', results['fusion']['predicted_emotion']])
            writer.writerow(['Confidence', f"{results['fusion']['confidence']:.2%}"])
            writer.writerow(['Duration (seconds)', f"{results.get('duration', 0):.1f}"])
        else:
            writer.writerow(['Predicted Emotion', results['combined']['predicted_emotion']])
            writer.writerow(['Confidence', f"{results['combined']['confidence']:.2%}"])
        writer.writerow([])
        
        # Modality Breakdown
        writer.writerow(['MODALITY BREAKDOWN'])
        writer.writerow(['Modality', 'Emotion', 'Confidence'])
        
        if is_video:
            visual_conf = max(results['visual']['aggregated_emotions'].values())
            writer.writerow(['Visual (Facial)', results['visual']['dominant_emotion'], f"{visual_conf:.2%}"])
        
        audio_conf = max(results['audio']['audio_emotions_7'].values())
        writer.writerow(['Audio (Voice)', results['audio']['dominant_emotion'], f"{audio_conf:.2%}"])
        
        text_conf = max(results['text']['text_emotions'].values())
        writer.writerow(['Text (Speech)', results['text']['dominant_emotion'], f"{text_conf:.2%}"])
        writer.writerow([])
        
        # Emotion Probabilities
        writer.writerow(['EMOTION PROBABILITIES'])
        writer.writerow(['Emotion', 'Probability'])
        
        probs = results['fusion']['probabilities'] if is_video else results['combined']['probabilities']
        for emotion, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([emotion.capitalize(), f"{prob:.2%}"])
        writer.writerow([])
        
        # Performance Metrics
        writer.writerow(['PERFORMANCE METRICS'])
        writer.writerow(['Metric', 'Score (0-100)'])
        writer.writerow(['Overall Performance', f"{metrics['overall']:.1f}"])
        writer.writerow(['Engagement', f"{metrics['engagement']:.1f}"])
        writer.writerow(['Confidence', f"{metrics['confidence']:.1f}"])
        writer.writerow(['Communication', f"{metrics['communication']:.1f}"])
        writer.writerow(['Positivity', f"{metrics['positivity']:.1f}"])
        writer.writerow(['Stress Level', f"{metrics['stress']:.1f}"])
        writer.writerow(['Emotional Stability', f"{metrics['stability']:.1f}"])
        writer.writerow([])
        
        # Transcript
        writer.writerow(['TRANSCRIPT'])
        transcript_text = results.get('transcript', {}).get('text', 'No speech detected')
        writer.writerow([transcript_text])
        writer.writerow([])
        
        # Word-level emotions
        if results.get('word_emotions'):
            writer.writerow(['WORD-LEVEL EMOTIONS'])
            writer.writerow(['Phrase', 'Emotion', 'Confidence'])
            for item in results['word_emotions']:
                writer.writerow([item['phrase'], item['emotion'], f"{item['confidence']:.2%}"])
            writer.writerow([])
        
        # Frame emotions (video only)
        if is_video and results['visual'].get('frame_emotions'):
            writer.writerow(['FRAME-BY-FRAME EMOTIONS'])
            writer.writerow(['Frame #', 'Emotion'])
            for i, emotion in enumerate(results['visual']['frame_emotions'], 1):
                writer.writerow([i, emotion])
            writer.writerow([])
        
        # Recommendations
        if metrics.get('recommendations'):
            writer.writerow(['RECOMMENDATIONS'])
            writer.writerow(['Category', 'Issue', 'Suggestion'])
            for rec in metrics['recommendations']:
                writer.writerow([rec['category'], rec['issue'], rec['suggestion']])
    
    return output_path

def get_export_bytes(file_path):
    """Read file and return bytes for download"""
    with open(file_path, 'rb') as f:
        return f.read()
