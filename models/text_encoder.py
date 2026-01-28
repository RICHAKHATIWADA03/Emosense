"""Text Encoder using HuggingFace Transformers"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List
import config

class TextEncoder:
    def __init__(self, model_name=None):
        self.model_name = model_name or config.TEXT_MODEL
        self.text_emotions = config.TEXT_EMOTIONS
        self.target_emotions = config.EMOTION_LABELS
        self._load_model()
    
    def _load_model(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()
        except Exception as e:
            print(f"Error loading model: {e}")
            self.tokenizer = None
            self.model = None
    
    def extract_emotion(self, text):
        if not text or len(text.strip()) == 0:
            return {emotion: 1.0/7 for emotion in self.target_emotions}
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=1)
            probs = probs.squeeze().cpu().numpy()
            emotion_probs = {}
            for i, emotion in enumerate(self.text_emotions):
                if i < len(probs):
                    emotion_probs[emotion] = float(probs[i])
            return self._map_emotions(emotion_probs)
        except Exception as e:
            return {emotion: 1.0/7 for emotion in self.target_emotions}
    
    def _map_emotions(self, model_emotions):
        mapped = {emotion: 0.0 for emotion in self.target_emotions}
        mapped['angry'] = model_emotions.get('anger', 0.0)
        mapped['disgust'] = model_emotions.get('disgust', 0.0)
        mapped['fear'] = model_emotions.get('fear', 0.0)
        mapped['happy'] = model_emotions.get('joy', 0.0)
        mapped['neutral'] = model_emotions.get('neutral', 0.0)
        mapped['sad'] = model_emotions.get('sadness', 0.0)
        mapped['surprise'] = model_emotions.get('surprise', 0.0)
        total = sum(mapped.values())
        if total > 0:
            mapped = {k: v/total for k, v in mapped.items()}
        else:
            mapped = {k: 1.0/7 for k in mapped.keys()}
        return mapped
    
    def get_emotion_vector(self, emotions):
        emotion_vector = [emotions.get(emotion, 0.0) for emotion in self.target_emotions]
        return torch.tensor([emotion_vector], dtype=torch.float32)
    
    def analyze_text(self, text):
        emotions = self.extract_emotion(text)
        emotion_tensor = self.get_emotion_vector(emotions)
        return {
            'features': emotion_tensor,
            'text_emotions': emotions,
            'dominant_emotion': max(emotions.items(), key=lambda x: x[1])[0],
            'text': text
        }
