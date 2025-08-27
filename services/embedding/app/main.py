import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from contextlib import asynccontextmanager
from llama_cpp import Llama

from .config import settings
settings.LOGS_DIR.mkdir(exist_ok=True)

file_handler = RotatingFileHandler(settings.LOG_FILE_PATH, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'))

# Configura o logger para também exibir no console (`docker logs`)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

model_state = {}

class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1)

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.EMBEDDING_MODEL_PATH or not settings.EMBEDDING_MODEL_PATH.exists():
        msg = f"Modelo de embedding não encontrado em {settings.EMB_DIR}"
        logging.critical(msg)
        raise FileNotFoundError(msg)

    logging.info(f"Carregando modelo de embedding: {settings.EMBEDDING_MODEL_PATH.name}")
    try:
        llm = Llama(
            model_path=str(settings.EMBEDDING_MODEL_PATH),
            n_ctx=settings.MAX_CONTEXT_LENGTH,
            embedding=True,
            n_threads=settings.N_THREADS,
            verbose=False
        )
        model_state["llm"] = llm
        logging.info(f"--- Serviço de Embedding pronto na porta {settings.PORT} ---")
        yield
    except Exception as e:
        logging.critical(f"Erro ao carregar modelo de embedding: {e}", exc_info=True)
        raise
    
    logging.info("--- Finalizando Serviço de Embedding ---")
    model_state.clear()

app = FastAPI(lifespan=lifespan)

@app.post("/embed", response_model=EmbedResponse)
def create_embeddings(request: EmbedRequest):
    llm = model_state.get("llm")
    if not llm:
        raise HTTPException(status_code=503, detail="Modelo não inicializado.")
    
    try:
        logging.info(f"Recebida requisição para embedar {len(request.texts)} textos.")
        embeddings_data = llm.create_embedding(request.texts)
        embeddings = [d["embedding"] for d in embeddings_data["data"]]
        logging.info("Embeddings criados com sucesso.")
        return EmbedResponse(embeddings=embeddings)
    except Exception as e:
        logging.error(f"Erro ao criar embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Falha ao processar textos.")

@app.get("/health")
def health_check():
    return {"status": "ok"}