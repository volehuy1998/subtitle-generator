# Set thread counts for CPU performance BEFORE any library imports
import os
import shutil
from pathlib import Path

CPU_COUNT = os.cpu_count() or 4
os.environ.setdefault("OMP_NUM_THREADS", str(CPU_COUNT))
os.environ.setdefault("MKL_NUM_THREADS", str(CPU_COUNT))

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent  # project root
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"
TEMPLATE_DIR = BASE_DIR / "templates"

# --- External dependencies ---
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
FFPROBE_AVAILABLE = shutil.which("ffprobe") is not None

# Extensions that require FFmpeg for audio extraction (video formats)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
AUDIO_ONLY_EXTENSIONS = {".mp3", ".wav", ".flac"}

# --- File validation ---
ALLOWED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov", ".mp3", ".wav", ".flac"}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
MIN_FILE_SIZE = 1024  # 1 KB minimum (reject empty/trivial files)
MAX_AUDIO_DURATION = 4 * 3600  # 4 hours max

# --- Subtitle file validation ---
ALLOWED_SUBTITLE_EXTENSIONS = {".srt", ".vtt"}
MAX_SUBTITLE_SIZE = 10 * 1024 * 1024  # 10 MB

# Allowed MIME types mapped from extensions
ALLOWED_MIME_PREFIXES = {"video/", "audio/", "application/octet-stream"}

# --- Whisper constants ---
MEL_HOP_LENGTH = 160
MEL_SAMPLE_RATE = 16000
SECONDS_PER_MEL_FRAME = MEL_HOP_LENGTH / MEL_SAMPLE_RATE  # 0.01s

# VRAM requirements (GB) per model with int8_float16 (faster-whisper)
MODEL_VRAM_GB = {
    "tiny":   0.5,
    "base":   0.8,
    "small":  1.5,
    "medium": 3.0,
    "large":  5.5,
}

VALID_MODELS = ["tiny", "base", "small", "medium", "large"]
VALID_DEVICES = ["cuda", "cpu"]

# --- Concurrency ---
MAX_CONCURRENT_TASKS = 3

# --- Rate limits ---
UPLOAD_RATE_LIMIT = "5/minute"
API_RATE_LIMIT = "60/minute"

# --- Performance ---
PRELOAD_MODEL = os.environ.get("PRELOAD_MODEL", "")  # e.g., "medium" to preload at startup
ENABLE_COMPRESSION = os.environ.get("ENABLE_COMPRESSION", "true").lower() == "true"
STATIC_CACHE_MAX_AGE = 3600  # 1 hour cache for static-like responses

# --- Task persistence (legacy, replaced by PostgreSQL in Sprint 18) ---
TASK_HISTORY_FILE = BASE_DIR / "task_history.json"
MAX_TASK_HISTORY = 100

# --- Database ---
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR / 'subtitle_generator.db'}",
)
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))

# --- Logging ---
LOG_OUTPUT = os.environ.get("LOG_OUTPUT", "both")  # stdout, file, both, json
LOG_JSON_ONLY = os.environ.get("LOG_JSON_ONLY", "false").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_WEBHOOK_URL = os.environ.get("LOG_WEBHOOK_URL", "")  # e.g., http://logstash:5000
LOG_SYSLOG_HOST = os.environ.get("LOG_SYSLOG_HOST", "")  # e.g., syslog.example.com:514

# --- Multi-server role ---
# "standalone" = single server (default), "web" = API only, "worker" = Celery worker only
ROLE = os.environ.get("ROLE", "standalone")

# --- Redis (shared state + Pub/Sub + Celery broker) ---
REDIS_URL = os.environ.get("REDIS_URL", "")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "") or REDIS_URL

# --- S3 / MinIO (shared file storage) ---
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")  # "local" or "s3"
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "subtitle-generator")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

# --- Environment mode ---
# "dev" = local development (HTTP, no HSTS), "prod" = production (HTTPS, HSTS)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
_is_prod = ENVIRONMENT == "prod"

# --- Security infrastructure ---
HSTS_ENABLED = os.environ.get("HSTS_ENABLED", str(_is_prod)).lower() == "true"
HTTPS_REDIRECT = os.environ.get("HTTPS_REDIRECT", str(_is_prod)).lower() == "true"
CSP_NONCE_ENABLED = os.environ.get("CSP_NONCE_ENABLED", "false").lower() == "true"
CORS_DEFAULT_DENY = os.environ.get("CORS_DEFAULT_DENY", "false").lower() == "true"

# --- Language support ---
# faster-whisper supported languages (ISO 639-1 codes)
SUPPORTED_LANGUAGES = {
    "auto": "Auto-detect",
    "en": "English", "zh": "Chinese", "de": "German", "es": "Spanish",
    "ru": "Russian", "ko": "Korean", "fr": "French", "ja": "Japanese",
    "pt": "Portuguese", "tr": "Turkish", "pl": "Polish", "ca": "Catalan",
    "nl": "Dutch", "ar": "Arabic", "sv": "Swedish", "it": "Italian",
    "id": "Indonesian", "hi": "Hindi", "fi": "Finnish", "vi": "Vietnamese",
    "he": "Hebrew", "uk": "Ukrainian", "el": "Greek", "ms": "Malay",
    "cs": "Czech", "ro": "Romanian", "da": "Danish", "hu": "Hungarian",
    "ta": "Tamil", "no": "Norwegian", "th": "Thai", "ur": "Urdu",
    "hr": "Croatian", "bg": "Bulgarian", "lt": "Lithuanian", "la": "Latin",
    "mi": "Maori", "ml": "Malayalam", "cy": "Welsh", "sk": "Slovak",
    "te": "Telugu", "fa": "Persian", "lv": "Latvian", "bn": "Bengali",
    "sr": "Serbian", "az": "Azerbaijani", "sl": "Slovenian", "kn": "Kannada",
    "et": "Estonian", "mk": "Macedonian", "br": "Breton", "eu": "Basque",
    "is": "Icelandic", "hy": "Armenian", "ne": "Nepali", "mn": "Mongolian",
    "bs": "Bosnian", "kk": "Kazakh", "sq": "Albanian", "sw": "Swahili",
    "gl": "Galician", "mr": "Marathi", "pa": "Punjabi", "si": "Sinhala",
    "km": "Khmer", "sn": "Shona", "yo": "Yoruba", "so": "Somali",
    "af": "Afrikaans", "oc": "Occitan", "ka": "Georgian", "be": "Belarusian",
    "tg": "Tajik", "sd": "Sindhi", "gu": "Gujarati", "am": "Amharic",
    "yi": "Yiddish", "lo": "Lao", "uz": "Uzbek", "fo": "Faroese",
    "ht": "Haitian Creole", "ps": "Pashto", "tk": "Turkmen", "nn": "Nynorsk",
    "mt": "Maltese", "sa": "Sanskrit", "lb": "Luxembourgish", "my": "Myanmar",
    "bo": "Tibetan", "tl": "Tagalog", "mg": "Malagasy", "as": "Assamese",
    "tt": "Tatar", "haw": "Hawaiian", "ln": "Lingala", "ha": "Hausa",
    "ba": "Bashkir", "jw": "Javanese", "su": "Sundanese", "yue": "Cantonese",
}
