"""
Configuration management for Stressor.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings
import yaml


class Settings(BaseSettings):
    """Main configuration settings for FailProof LLM."""
    
    # API Keys (encrypted in production)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./stressor.db", env="DATABASE_URL")
    
    # Security Settings
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    encryption_key: str = Field(..., env="ENCRYPTION_KEY", min_length=32)
    
    # Rate Limiting
    max_requests_per_minute: int = Field(60, env="MAX_REQUESTS_PER_MINUTE")
    max_requests_per_hour: int = Field(1000, env="MAX_REQUESTS_PER_HOUR")
    
    # Storage Settings
    data_directory: Path = Field(Path("./data"), env="DATA_DIRECTORY")
    log_directory: Path = Field(Path("./logs"), env="LOG_DIRECTORY")
    backup_directory: Path = Field(Path("./backups"), env="BACKUP_DIRECTORY")
    
    # Dashboard Settings
    dashboard_host: str = Field("0.0.0.0", env="DASHBOARD_HOST")
    dashboard_port: int = Field(8080, env="DASHBOARD_PORT")
    dashboard_secret_key: str = Field(..., env="DASHBOARD_SECRET_KEY")
    
    # Testing Configuration
    default_model: str = Field("gpt-5", env="DEFAULT_MODEL")
    default_max_tokens: int = Field(2048, env="DEFAULT_MAX_TOKENS")
    default_temperature: float = Field(0.1, env="DEFAULT_TEMPERATURE")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Monitoring
    enable_monitoring: bool = Field(True, env="ENABLE_MONITORING")
    monitoring_endpoint: str = Field("http://localhost:9090", env="MONITORING_ENDPOINT")
    
    # Development Settings
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")
    
    @validator("data_directory", "log_directory", "backup_directory", pre=True)
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("secret_key", "encryption_key")
    def validate_key_length(cls, v):
        """Validate key lengths for security."""
        if len(v) < 32:
            raise ValueError("Key must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": self.database_url,
            "echo": self.debug,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return {
            "data_directory": self.data_directory,
            "log_directory": self.log_directory,
            "backup_directory": self.backup_directory,
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "secret_key": self.secret_key,
            "encryption_key": self.encryption_key,
            "rate_limit_per_minute": self.max_requests_per_minute,
            "rate_limit_per_hour": self.max_requests_per_hour,
        }
    
    @classmethod
    def load_from_file(cls, config_path: str) -> "Settings":
        """Load settings from a YAML configuration file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Override with environment variables
        return cls(**config_data) 


# Global settings instance
settings = Settings() 