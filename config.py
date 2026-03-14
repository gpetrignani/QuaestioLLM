from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
ARTIFACT_DIR = DATA_DIR / "artifacts"
DB_PATH = DATA_DIR / "quaestio_documents.db"

OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
LLM_TIMEOUT_SECONDS = 90
MAX_VALIDATION_RETRIES = 3
MAX_TEXT_CHARS = 18000

SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".txt"}


def ensure_directories() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)
