import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path('/app')
    MODELS_DIR = BASE_DIR / "models"
    EMB_DIR = MODELS_DIR / "embeddings"
    LOGS_DIR = BASE_DIR / "app" / "logs"

    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

    try:
        EMBEDDING_MODEL_PATH = next(EMB_DIR.glob(f"*{EMBEDDING_MODEL_NAME}*.gguf"))
    except (StopIteration, TypeError):
        EMBEDDING_MODEL_PATH = None

    N_THREADS = int(os.getenv("N_THREADS", "4"))
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
    PORT = int(os.getenv("PORT", "8001"))

    LOG_FILE_PATH = LOGS_DIR / "embedding_service.log"

settings = Config()