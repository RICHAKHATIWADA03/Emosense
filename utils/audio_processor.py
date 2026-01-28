"""Audio Processing with Whisper"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict
import whisper
import config

class AudioProcessor:
    def __init__(self, whisper_model=None):
        self.whisper_model_name = whisper_model or config.WHISPER_MODEL
        self.whisper_model = None
        self.sample_rate = config.AUDIO_SAMPLE_RATE
        
    def _load_whisper(self):
        if self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model(self.whisper_model_name)
            except Exception as e:
                print(f"Error loading Whisper: {e}")
    
    def extract_audio_from_video(self, video_path, output_path=None):
        if output_path is None:
            video_path_obj = Path(video_path)
            output_path = config.TEMP_DIR / f"{video_path_obj.stem}_audio.wav"
        output_path = Path(output_path)
        try:
            command = [
                'ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate), '-ac', '1', '-y', str(output_path)
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return None
            if output_path.exists() and output_path.stat().st_size > 0:
                return str(output_path)
            return None
        except Exception as e:
            return None
    
    def transcribe_audio(self, audio_path):
        self._load_whisper()
        if self.whisper_model is None:
            return {'text': '', 'segments': [], 'language': 'en', 'error': 'Whisper not loaded'}
        try:
            result = self.whisper_model.transcribe(str(audio_path), language='en', task='transcribe')
            transcript = result['text'].strip()
            segments = result.get('segments', [])
            return {
                'text': transcript,
                'segments': segments,
                'language': result.get('language', 'en'),
                'duration': sum([seg['end'] - seg['start'] for seg in segments])
            }
        except Exception as e:
            return {'text': '', 'segments': [], 'language': 'en', 'error': str(e)}
    
    def process_video(self, video_path):
        audio_path = self.extract_audio_from_video(video_path)
        if audio_path is None:
            return {
                'audio_path': None,
                'transcript': {'text': '', 'segments': [], 'error': config.ERROR_MESSAGES['no_audio']}
            }
        transcript = self.transcribe_audio(audio_path)
        return {'audio_path': audio_path, 'transcript': transcript}
