"""
Конфигурация приложения NFT Gifts
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = "8494126901:AAE0fbTFsQosqG1YpoGjx9SkIM41PzB64RQ"
    
    # Admin Configuration
    ADMIN_IP: str = "80.64.26.253"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./nft_gifts.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
