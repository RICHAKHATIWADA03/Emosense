"""Visual Encoder using HSEmotion - Fast and accurate"""
import torch
import numpy as np
from hsemotion.facial_emotions import HSEmotionRecognizer
import cv2
import config

class VisualEncoder:
    def __init__(self, model_name=None, backend=None):
        self.emotion_labels = config.EMOTION_LABELS
        print("Initializing HSEmotion detector...")
        self.detector = HSEmotionRecognizer(model_name='enet_b0_8_best_afew')
        print("HSEmotion loaded")
        
        # HSEmotion outputs: Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise
        self.hsemotion_to_our = {
            'Anger': 'angry',
            'Disgust': 'disgust',
            'Fear': 'fear',
            'Happiness': 'happy',
            'Sadness': 'sad',
            'Surprise': 'surprise',
            'Neutral': 'neutral',
            'Contempt': None  # ignore
        }
        
    def extract_from_frame(self, frame):
        try:
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Detect face and get emotions
            emotion, scores = self.detector.predict_emotions(frame_bgr, logits=False)
            
            if emotion is None:
                return None
            
            # Map to our 7 emotions
            mapped = {e: 0.0 for e in self.emotion_labels}
            
            # scores is a list of probabilities for each emotion
            hsemotion_labels = ['Anger', 'Contempt', 'Disgust', 'Fear', 'Happiness', 'Neutral', 'Sadness', 'Surprise']
            
            for i, score in enumerate(scores):
                hs_label = hsemotion_labels[i]
                our_label = self.hsemotion_to_our.get(hs_label)
                if our_label:
                    mapped[our_label] = float(score)
            
            return mapped
            
        except Exception as e:
            print(f"HSEmotion error: {e}")
            return None
    
    def analyze_video_frames(self, frames):
        print(f"Analyzing {len(frames)} frames with HSEmotion")
        
        if len(frames) == 0:
            return self._get_default_result()
        
        # Sample 3 frames
        indices = [0, len(frames)//2, len(frames)-1] if len(frames) >= 3 else [0]
        
        all_emotions = []
        for idx in indices:
            emotions = self.extract_from_frame(frames[idx])
            if emotions:
                all_emotions.append(emotions)
        
        if not all_emotions:
            return self._get_default_result()
        
        # Average
        aggregated = {e: sum(em[e] for em in all_emotions)/len(all_emotions) for e in self.emotion_labels}
        
        print(f"Detected {len(all_emotions)}/{len(indices)} faces")
        
        return {
            'features': torch.tensor([[aggregated[e] for e in self.emotion_labels]], dtype=torch.float32),
            'aggregated_emotions': aggregated,
            'frame_emotions': all_emotions,
            'detected_frames': len(all_emotions),
            'detection_rate': len(all_emotions) / len(indices),
            'dominant_emotion': max(aggregated.items(), key=lambda x: x[1])[0]
        }
    
    def _get_default_result(self):
        default_emotions = {e: 1.0/7 for e in self.emotion_labels}
        return {
            'features': torch.tensor([[1.0/7]*7], dtype=torch.float32),
            'aggregated_emotions': default_emotions,
            'frame_emotions': [],
            'detected_frames': 0,
            'detection_rate': 0.0,
            'dominant_emotion': 'neutral'
        }
