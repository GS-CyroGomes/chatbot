import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path('/app')
    MODELS_DIR = BASE_DIR / "models"
    AGENTS_DIR = MODELS_DIR / "agents"
    LOGS_DIR = BASE_DIR / "app" / "logs"

    AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME")

    try:
        AGENT_MODEL_PATH = next(AGENTS_DIR.glob(f"*{AGENT_MODEL_NAME}*.gguf"))
    except (StopIteration, TypeError):
        AGENT_MODEL_PATH = None

    N_THREADS = int(os.getenv("N_THREADS", "4"))
    N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
    PORT = int(os.getenv("PORT", "8002"))

    LOG_FILE_PATH = LOGS_DIR / "generator_service.log"

settings = Config()