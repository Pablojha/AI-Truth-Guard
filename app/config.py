import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Provider mode
    PROVIDER_MODE = os.getenv("PROVIDER_MODE", "fixture")

    # Ollama
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "1"))

    # Versions
    CORPUS_VERSION = os.getenv("CORPUS_VERSION", "v0.1")
    PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v0.1")

    # Limits
    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "5000"))
    MAX_CLAIMS_PER_REQUEST = int(os.getenv("MAX_CLAIMS_PER_REQUEST", "20"))
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

    # Database (PostgreSQL for production, SQLite for development)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./truthguard.db")

    # For Vercel production, convert postgres:// to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Payments (UPI)
    UPI_ID = os.getenv("UPI_ID", "")
    UPI_PAYEE_NAME = os.getenv("UPI_PAYEE_NAME", "AI TruthGuard")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    PAYMENT_MODE = os.getenv("PAYMENT_MODE", "upi")
    ADMIN_DEMO_ID = os.getenv("ADMIN_DEMO_ID", "demo-admin")

    # Production check
    IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"


config = Config()

if (config.IS_PRODUCTION or os.getenv("VERCEL")) and config.SECRET_KEY == "dev-secret-key-change-in-production":
    raise RuntimeError(
        "SECRET_KEY is not set. Add it to the hosting environment variables, then redeploy."
    )
