import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("ALUMNI_DB", BASE_DIR / "alumni.db"))
UPLOAD_DIR = Path(os.getenv("ALUMNI_UPLOADS", BASE_DIR / "uploads"))

# Both services must share this secret so a token issued by Flask is valid on FastAPI.
JWT_SECRET = os.getenv("ALUMNI_JWT_SECRET", "dev-only-change-me-alumni-connect-secret")
ACCESS_TTL_SECONDS = 3600
REFRESH_TTL_SECONDS = 7 * 24 * 3600

MAX_POSTER_BYTES = 1_536_000  # 1.5 MB, per report section 3.2
ALLOWED_POSTER_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
