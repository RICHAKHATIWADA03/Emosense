"""Configuration for EmoSense - Streamlit Cloud Compatible"""
from pathlib import Path
import os
import re

# Application settings
PAGE_TITLE = "EmoSense Emotion Analyzer"
PAGE_ICON = "🎭"
LAYOUT = "wide"

# Paths
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# Emotion settings
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

COLOR_SCHEME = {
    'angry': '#FF6B6B',
    'disgust': '#95E1D3',
    'fear': '#A8E6CF',
    'happy': '#FFD93D',
    'sad': '#6C5CE7',
    'surprise': '#FFA07A',
    'neutral': '#95A5A6'
}

# Model settings
SPEECHBRAIN_MODEL = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"
TEXT_MODEL = "j-hartmann/emotion-english-distilroberta-base"
HSEMOTION_MODEL = "enet_b0_8_best_afew"
WHISPER_MODEL = "tiny"

# Audio emotion mapping
AUDIO_EMOTIONS = {'neu': 'neutral', 'hap': 'happy', 'ang': 'angry', 'sad': 'sad'}
TEXT_EMOTIONS = ['anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise']
TEXT_EMOTION_MAP = {
    'anger': 'angry', 'disgust': 'disgust', 'fear': 'fear',
    'joy': 'happy', 'neutral': 'neutral', 'sadness': 'sad', 'surprise': 'surprise'
}

# Video/Audio settings
MAX_VIDEO_DURATION = 120
VIDEO_FPS = 30
TARGET_FPS = 0.5
MAX_FRAMES = 100
MIN_VIDEO_DURATION = 1
MIN_RECORDING_DURATION = 5
MAX_RECORDING_DURATION = 120
DEFAULT_RECORDING_DURATION = 15

# Feature extraction
FACE_DETECTION_CONFIDENCE = 0.5
MIN_FACE_SIZE = 30
AUDIO_SAMPLE_RATE = 16000

# Fusion weights
FUSION_WEIGHTS = {'visual': 0.3, 'audio': 0.2, 'text': 0.5}

# Thresholds
CONFIDENCE_THRESHOLD = 0.5
MIN_AUDIO_CONFIDENCE = 0.3
MIN_FACE_CONFIDENCE = 0.5
MIN_TEXT_CONFIDENCE = 0.3
MIN_EMOTION_CONFIDENCE = 0.4
NERVOUSNESS_THRESHOLD = 0.6
ENGAGEMENT_THRESHOLD = 0.5
POSITIVITY_THRESHOLD = 0.6

# Emotion groupings
NERVOUSNESS_EMOTIONS = ['fear', 'surprise']
ENGAGEMENT_EMOTIONS = ['happy', 'surprise']
POSITIVE_EMOTIONS = ['happy']
NEGATIVE_EMOTIONS = ['angry', 'sad', 'fear', 'disgust']

# Processing settings
FRAME_SKIP = 2
KEY_FRAME_INDICES = [0, 0.5, 1.0]
AUDIO_CHUNK_SIZE = 16000 * 10
MAX_AUDIO_LENGTH = 300
WHISPER_LANGUAGE = "en"
WHISPER_TASK = "transcribe"

# Display settings
MAX_TRANSCRIPT_LENGTH = 5000
WORD_WINDOW_SIZE = 5
CHART_HEIGHT = 400
CHART_WIDTH = 800
TIMELINE_HEIGHT = 300

# Detection settings
ENABLE_FACE_DETECTION = True
ENABLE_AUDIO_DETECTION = True
ENABLE_TEXT_DETECTION = True

# Metric weights
METRIC_WEIGHTS = {'confidence': 0.3, 'nervousness': 0.2, 'engagement': 0.25, 'positivity': 0.25}

# File formats
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac']

# File size limits
MAX_VIDEO_SIZE_MB = 500
MAX_AUDIO_SIZE_MB = 100

# Subscription tiers
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free', 'price': 0, 'max_recording_duration': 30,
        'max_upload_size_mb': 50, 'max_history': 10, 'advanced_metrics': False
    },
    'premium': {
        'name': 'Premium', 'price': 9.99, 'max_recording_duration': 120,
        'max_upload_size_mb': 500, 'max_history': 999999, 'advanced_metrics': True
    }
}

# PostgreSQL Database - Streamlit Cloud Compatible
DATABASE_URL = ''

# Try Streamlit secrets first (for Streamlit Cloud)
try:
    import streamlit as st
    if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
        DATABASE_URL = st.secrets['DATABASE_URL']
except:
    pass

# Fall back to environment variable
if not DATABASE_URL:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL', '')

# Parse connection string
POSTGRES_CONFIG = {
    'host': 'localhost', 'port': 5432, 'database': 'emosense_db',
    'user': 'postgres', 'password': ''
}

if DATABASE_URL:
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, DATABASE_URL)
    if match:
        POSTGRES_CONFIG = {
            'user': match.group(1), 'password': match.group(2),
            'host': match.group(3), 'port': int(match.group(4)),
            'database': match.group(5)
        }
