import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables with safe defaults.

    NOTE: For production, set a secure ADMIN_PASSWORD and BOT_TOKEN via environment variables.
    """

    def __init__(self) -> None:
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        self.bot_token: str = os.getenv(
            "BOT_TOKEN",
            # Provided by the user prompt; consider rotating for production.
            "8494126901:AAE0fbTFsQosqG1YpoGjx9SkIM41PzB64RQ",
        )
        self.admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
        # IP allowed to access admin UI
        self.admin_allowed_ip: str = os.getenv("ADMIN_ALLOWED_IP", "80.64.26.253")
        self.static_dir: str = os.getenv("STATIC_DIR", "app/static")
        self.templates_dir: str = os.getenv("TEMPLATES_DIR", "app/templates")
        self.app_title: str = os.getenv("APP_TITLE", "NFT Gifts Store")


settings = Settings()
