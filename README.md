# EmoSense Interview Analyzer

Multimodal emotion recognition system for analyzing interview videos.

## Features
- Analyzes facial expressions, voice tone, and speech content
- Detects 7 emotions: angry, disgust, fear, happy, sad, surprise, neutral
- Interview metrics: confidence, nervousness, engagement, enthusiasm
- Cross-attention fusion model for combining modalities

## Installation
Already installed in conda environment 'mvp'

## Usage
1. Add your trained model to: assets/checkpoints/cross_attention_model.pth
2. Run: streamlit run app.py
3. Upload interview video (max 30 seconds)
4. Click "Analyze Interview"

## Models
- Visual: DeepFace
- Audio: SpeechBrain wav2vec2-IEMOCAP
- Text: DistilRoBERTa
- Transcription: Whisper
- Fusion: Cross-Attention (your trained model)

## Requirements
- Python 3.9
- FFmpeg
- All packages installed in conda environment
