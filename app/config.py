import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings:
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    pprof_enabled: bool = os.getenv("PPROF", "false").lower() == "true"
    secret_token: str = os.getenv("SECRET_TOKEN", "")

    # Suno account
    session_id: str = os.getenv("SESSION_ID", "")
    cookie: str = os.getenv("COOKIE", "")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./api.db")

    # External API
    base_url: str = os.getenv("BASE_URL", "https://studio-api.suno.ai")
    exchange_token_url: str = os.getenv(
        "EXCHANGE_TOKEN_URL",
        "https://clerk.suno.com/v1/client/sessions/{}/tokens?_clerk_js_version=4.73.2",
    )

    # Chat settings
    chat_openai_model: str = os.getenv("CHAT_OPENAI_MODEL", "gpt-4o")
    chat_openai_base: str = os.getenv("CHAT_OPENAI_BASE", "https://api.openai.com")
    chat_openai_key: str = os.getenv("CHAT_OPENAI_KEY", "")
    chat_template_dir: str = os.getenv("CHAT_TEMPLATE_DIR", "./template")
    # Timeout for blocking chat/lyrics generation in submit_lyrics
    chat_timeout: int = int(os.getenv("CHAT_TIME_OUT", "600"))
    # Timeout for polling Suno tasks in background loops (seconds)
    poll_timeout: int = int(os.getenv("POLL_TIMEOUT", "600"))

    # Networking & Logging
    proxy: str = os.getenv("PROXY", "") or None
    log_dir: str = os.getenv("LOG_DIR", "./logs")
    rotate_logs: bool = os.getenv("ROTATE_LOGS", "false").lower() == "true"

    # Version info
    version: str = os.getenv("VERSION", "0.0.0")

settings = Settings()