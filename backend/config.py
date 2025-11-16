"""Application configuration."""
import os
from pathlib import Path

# Backward compatibility constants for existing code
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIOGRAMS_DIR = DATA_DIR / "audiograms"
DB_PATH = DATA_DIR / "hearing_tests.db"  # Backward compatibility

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
AUDIOGRAMS_DIR.mkdir(exist_ok=True)

# OCR confidence threshold
OCR_CONFIDENCE_THRESHOLD = 0.8

# Audiometric standard frequencies (Hz)
STANDARD_FREQUENCIES = [64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]


class Config:
    """Base configuration."""

    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Database
    DB_PATH = Path(os.getenv('DB_PATH', 'data/hearing_tests.db'))

    # File Upload
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', 'data/uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # CORS
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    def __init__(self):
        super().__init__()
        # Re-read from environment to ensure values are current
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', self.SECRET_KEY)
        cors_origins_str = os.getenv('CORS_ALLOWED_ORIGINS', '')
        self.CORS_ALLOWED_ORIGINS = cors_origins_str.split(',') if cors_origins_str else []

        # Validate required settings
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")
        if self.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("Cannot use development SECRET_KEY in production")
        if not self.CORS_ALLOWED_ORIGINS or self.CORS_ALLOWED_ORIGINS == ['']:
            raise ValueError("CORS_ALLOWED_ORIGINS must be set in production")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SECRET_KEY = 'test-secret-key'
    DB_PATH = Path(':memory:')  # In-memory database for tests
    UPLOAD_FOLDER = Path('/tmp/test_uploads')


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development')

    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
