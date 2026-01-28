"""Text Analysis with Word-Level Emotion Detection"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import config

class WordLevelEmotionAnalyzer:
    def __init__(self, model_name=None):
        self.model_name = model_name or config.TEXT_MODEL
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.eval()
        self.text_emotions = config.TEXT_EMOTIONS
        self.target_emotions = config.EMOTION_LABELS
    
    def analyze_word(self, word):
        """Analyze emotion for a single word"""
        if not word or len(word.strip()) < 2:
            return None
        
        try:
            inputs = self.tokenizer(word, return_tensors="pt", truncation=True, padding=True)
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
        except:
            return None
    
    def _map_emotions(self, model_emotions):
        """Map model emotions to our 7 emotions"""
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
    
    def analyze_phrases(self, text, window_size=5):
        """Analyze text in sliding windows of words"""
        if not text or len(text.strip()) == 0:
            return []
        
        # Split into words
        words = re.findall(r'\b\w+\b|[.,!?;]', text)
        
        phrase_emotions = []
        
        for i in range(0, len(words), window_size):
            phrase = ' '.join(words[i:i+window_size])
            
            try:
                inputs = self.tokenizer(phrase, return_tensors="pt", truncation=True, max_length=512, padding=True)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probs = torch.nn.functional.softmax(logits, dim=1)
                
                probs = probs.squeeze().cpu().numpy()
                emotion_probs = {}
                for j, emotion in enumerate(self.text_emotions):
                    if j < len(probs):
                        emotion_probs[emotion] = float(probs[j])
                
                mapped_emotions = self._map_emotions(emotion_probs)
                dominant_emotion = max(mapped_emotions.items(), key=lambda x: x[1])
                
                phrase_emotions.append({
                    'phrase': phrase,
                    'start_word': i,
                    'end_word': min(i + window_size, len(words)),
                    'emotion': dominant_emotion[0],
                    'confidence': dominant_emotion[1],
                    'all_emotions': mapped_emotions
                })
            except:
                continue
        
        return phrase_emotions
    
    def highlight_transcript(self, text, window_size=5):
        """Create HTML highlighted transcript"""
        phrase_emotions = self.analyze_phrases(text, window_size)
        
        if not phrase_emotions:
            return text, []
        
        # Split text into words
        words = re.findall(r'\b\w+\b|[.,!?;]', text)
        
        # Create highlighted HTML
        highlighted_words = []
        
        for phrase_data in phrase_emotions:
            highlighted_words.append({
                'phrase': phrase_data['phrase'],
                'emotion': phrase_data['emotion'],
                'confidence': phrase_data['confidence']
            })
        
        return highlighted_words
