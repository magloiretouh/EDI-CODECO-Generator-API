"""
Configuration module for EDI Generator Flask application.
Loads environment variables from .env file and provides configuration objects.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Config:
    """Base configuration class."""

    # Flask settings
    ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Output directory configuration
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')

    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # SFTP Configuration
    SFTP_HOST = os.getenv('SFTP_HOST')
    SFTP_PORT = int(os.getenv('SFTP_PORT', '22'))
    SFTP_USER = os.getenv('SFTP_USER')
    SFTP_PASSWORD = os.getenv('SFTP_PASSWORD')
    SFTP_REMOTE_DIR = os.getenv('SFTP_REMOTE_DIR', '/')

    # SFTP Retry configuration
    SFTP_MAX_RETRIES = int(os.getenv('SFTP_MAX_RETRIES', '3'))
    SFTP_RETRY_DELAY = int(os.getenv('SFTP_RETRY_DELAY', '1'))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    OUTPUT_DIR = './test_output'
    # Ensure test output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# Select configuration based on environment
config = DevelopmentConfig() if Config.ENV == 'development' else ProductionConfig()
