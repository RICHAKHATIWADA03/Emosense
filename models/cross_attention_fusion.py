"""Simple weighted fusion without trained model"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import config

class CrossAttentionFusion(nn.Module):
    def __init__(self):
        super(CrossAttentionFusion, self).__init__()
        
    def forward(self, visual_features, audio_features, text_features):
        # Map audio (4-dim) to 7-dim
        audio_7dim = self._map_audio_to_7(audio_features)
        
        # Weighted average: visual=0.3, audio=0.2, text=0.5
        fused = (visual_features * 0.3 + audio_7dim * 0.2 + text_features * 0.5)
        
        return fused, {}
    
    def _map_audio_to_7(self, audio_4):
        # Map 4 IEMOCAP emotions to 7
        audio_7 = torch.zeros(audio_4.size(0), 7)
        audio_7[:, 0] = audio_4[:, 0]  # angry
        audio_7[:, 3] = audio_4[:, 1]  # happy
        audio_7[:, 4] = audio_4[:, 2]  # sad
        audio_7[:, 6] = audio_4[:, 3]  # neutral
        return audio_7
    
    def predict(self, visual_features, audio_features, text_features):
        self.eval()
        with torch.no_grad():
            logits, _ = self.forward(visual_features, audio_features, text_features)
            probs = F.softmax(logits, dim=1)
            confidence, predicted_idx = torch.max(probs, dim=1)
            predicted_emotion = config.EMOTION_LABELS[predicted_idx.item()]
            prob_dict = {emotion: probs[0, i].item() for i, emotion in enumerate(config.EMOTION_LABELS)}
            
            return {
                'predicted_emotion': predicted_emotion,
                'confidence': confidence.item(),
                'probabilities': prob_dict,
                'attention_info': {'fusion_weights': {'visual': 0.3, 'audio': 0.2, 'text': 0.5}},
                'modality_predictions': {}
            }

def load_cross_attention_model(checkpoint_path=None):
    model = CrossAttentionFusion()
    print("Using simple weighted fusion (0.3 visual + 0.2 audio + 0.5 text)")
    model.eval()
    return model
