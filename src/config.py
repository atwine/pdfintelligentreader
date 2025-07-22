"""
Configuration management for PDF Intelligent Reader
"""

import os
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./pdf_reader.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/pdf_reader.log", env="LOG_FILE")
    
    # Processing Configuration
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    batch_size: int = Field(10, env="BATCH_SIZE")
    processing_timeout: int = Field(300, env="PROCESSING_TIMEOUT")
    
    # Quality Thresholds
    min_sentence_completeness: float = Field(0.95, env="MIN_SENTENCE_COMPLETENESS")
    min_translation_readiness: float = Field(0.90, env="MIN_TRANSLATION_READINESS")
    max_noise_threshold: float = Field(0.05, env="MAX_NOISE_THRESHOLD")
    
    # Development Settings
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def setup_logging(settings: Settings) -> None:
    """Configure logging with loguru"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    logger.add(
        sink=settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    logger.info("Logging configured successfully")


# Global settings instance
settings = Settings()
setup_logging(settings)
