import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    """Configuration settings for the Notes Summarizer"""
    
    # API Keys 
    PINECONE_API_KEY:    str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME:  str
    OPENAI_API_KEY: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file       = ".env",       # if you use load_dotenv you can omit this
        extra          = "ignore",
    )
    # Model Settings
    USE_GPU: bool = True
    PADDLE_OCR_LANG: str = "en"
    CONFIDENCE_THRESHOLD: float = 0.8
    
    # Processing Settings
    MAX_IMAGE_SIZE: int = 2048
    DPI: int = 300
    
    # Content Type Detection Thresholds
    TABLE_LINE_THRESHOLD: int = 100
    MATH_SYMBOL_THRESHOLD: int = 3
    CODE_PATTERN_THRESHOLD: int = 2
    
    # File Paths
    TEMP_DIR: Path = Path("temp")
    OUTPUT_DIR: Path = Path("output")
    MODELS_DIR: Path = Path("models")
    
    # Supported File Types
    SUPPORTED_FORMATS: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]
    
    # OpenAI Settings (only for diagrams)
    OPENAI_MODEL: str = "gpt-4-vision-preview"
    OPENAI_MAX_TOKENS: int = 500
    
    # Table Extraction Settings
    TABLE_DETECTION_MODEL: str = "microsoft/table-transformer-structure-recognition"
    
    # Math OCR Settings
    MATH_OCR_MODEL: str = "facebook/nougat-base"
    

# Global settings instance
settings = Settings()

# Create necessary directories
settings.TEMP_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.MODELS_DIR.mkdir(exist_ok=True)