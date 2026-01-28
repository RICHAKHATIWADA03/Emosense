"""Audio emotion encoder using librosa and a simpler approach"""
import torch
import librosa
import numpy as np
import config

class AudioEncoder:
    def __init__(self):
        """Initialize with acoustic feature extraction"""
        print("Audio encoder initialized (using acoustic features)")
        self.sample_rate = 16000
    
    def analyze_audio(self, audio_path):
        """Analyze audio and return emotion probabilities based on acoustic features"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract acoustic features
            # 1. Energy/Intensity (correlates with angry, happy)
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            # 2. Pitch/Fundamental frequency (correlates with emotional arousal)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # 3. Zero crossing rate (correlates with voice quality)
            zcr = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # 4. Spectral features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            
            # 5. MFCC (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            
            # Simple rule-based emotion classification based on acoustic features
            # Normalize features
            energy_norm = min(energy * 10, 1.0)
            pitch_norm = min(pitch_mean / 500, 1.0) if pitch_mean > 0 else 0.5
            zcr_norm = min(zcr * 10, 1.0)
            
            # Map features to emotions (simplified heuristics)
            probabilities = {}
            
            # High energy + high pitch = angry or happy
            # Low energy + low pitch = sad
            # Medium values = neutral
            
            # Angry: high energy, high pitch, high ZCR
            probabilities['ang'] = (energy_norm * 0.4 + pitch_norm * 0.3 + zcr_norm * 0.3)
            
            # Happy: high energy, moderate-high pitch
            probabilities['hap'] = (energy_norm * 0.5 + pitch_norm * 0.3 + (1 - zcr_norm) * 0.2)
            
            # Sad: low energy, low pitch
            probabilities['sad'] = ((1 - energy_norm) * 0.5 + (1 - pitch_norm) * 0.5)
            
            # Neutral: moderate everything
            neutral_score = 1.0 - abs(energy_norm - 0.5) - abs(pitch_norm - 0.5)
            probabilities['neu'] = max(neutral_score, 0.2)
            
            # Normalize probabilities
            total = sum(probabilities.values())
            if total > 0:
                probabilities = {k: v/total for k, v in probabilities.items()}
            else:
                probabilities = {'neu': 0.4, 'hap': 0.2, 'ang': 0.2, 'sad': 0.2}
            
            # Map to our 7 emotions
            audio_emotions_7 = {
                'angry': probabilities.get('ang', 0.0),
                'happy': probabilities.get('hap', 0.0),
                'sad': probabilities.get('sad', 0.0),
                'neutral': probabilities.get('neu', 0.0),
                'disgust': 0.0,
                'fear': probabilities.get('ang', 0.0) * 0.3,  # Some overlap with anger
                'surprise': probabilities.get('hap', 0.0) * 0.2  # Some overlap with happy
            }
            
            # Normalize
            total = sum(audio_emotions_7.values())
            if total > 0:
                audio_emotions_7 = {k: v/total for k, v in audio_emotions_7.items()}
            
            # Get dominant emotion
            dominant_emotion = max(audio_emotions_7.items(), key=lambda x: x[1])[0]
            
            # Create feature vector for fusion (4-dim)
            features = torch.FloatTensor([
                probabilities.get('neu', 0.0),
                probabilities.get('hap', 0.0),
                probabilities.get('ang', 0.0),
                probabilities.get('sad', 0.0)
            ]).unsqueeze(0)
            
            return {
                'features': features,
                'audio_emotions_7': audio_emotions_7,
                'dominant_emotion': dominant_emotion,
                'raw_probabilities': probabilities
            }
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
            import traceback
            traceback.print_exc()
            
            # Return neutral if error
            return {
                'features': torch.ones(1, 4) / 4,
                'audio_emotions_7': {e: 1.0/7 for e in config.EMOTION_LABELS},
                'dominant_emotion': 'neutral',
                'raw_probabilities': {}
            }
