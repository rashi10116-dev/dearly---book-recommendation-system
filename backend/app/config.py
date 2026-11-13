import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project directories
base_dir = Path(__file__).resolve().parent.parent  # DEARLY/backend
root_dir = base_dir.parent                         # DEARLY

# Check both backend/.env and root .env so user configuration in either location is respected
if (base_dir / ".env").exists():
    load_dotenv(dotenv_path=base_dir / ".env", override=True)
elif (root_dir / ".env").exists():
    load_dotenv(dotenv_path=root_dir / ".env", override=True)
else:
    load_dotenv(override=True)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

# JWT and Authentication Security
DEFAULT_DEV_SECRET = "dearly_default_dev_key_never_use_in_prod_123456789"
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if not SECRET_KEY:
    if ENVIRONMENT == "production":
        raise ValueError("CRITICAL: SECRET_KEY environment variable is required in production mode.")
    SECRET_KEY = DEFAULT_DEV_SECRET
elif ENVIRONMENT == "production" and (SECRET_KEY == DEFAULT_DEV_SECRET or len(SECRET_KEY) < 32):
    raise ValueError("CRITICAL: Insecure or too-short SECRET_KEY detected in production mode. Must be at least 32 characters.")

ALGORITHM = os.getenv("ALGORITHM", "HS256").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    if ENVIRONMENT == "production":
        raise ValueError("CRITICAL: DATABASE_URL is required in production and must point to a PostgreSQL instance.")
    # Local fallback for development/testing if no URL supplied
    DATABASE_URL = f"sqlite:///{root_dir / 'dearly.db'}"

# Normalize postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Third-Party Book APIs Configuration
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip() or None
OPEN_LIBRARY_BASE_URL = os.getenv("OPEN_LIBRARY_BASE_URL", "https://openlibrary.org").rstrip("/")
GOOGLE_BOOKS_BASE_URL = os.getenv("GOOGLE_BOOKS_BASE_URL", "https://www.googleapis.com/books/v1").rstrip("/")

# CORS Configuration
ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
ALLOWED_ORIGINS = [orig.strip() for orig in ALLOWED_ORIGINS_STR.split(",") if orig.strip()]

if ENVIRONMENT == "production" and "*" in ALLOWED_ORIGINS:
    raise ValueError("CRITICAL: Wildcard CORS allowed_origins ('*') is forbidden in production mode.")

# File upload limits
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))) # 10 MB
MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "5000"))
