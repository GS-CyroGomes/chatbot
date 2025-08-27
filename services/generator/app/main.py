import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from llama_cpp import Llama

from .config import settings

settings.LOGS_DIR.mkdir(exist_ok=True)
file_handler = RotatingFileHandler(settings.LOG_FILE_PATH, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)


model_state = {}

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.AGENT_MODEL_PATH or not settings.AGENT_MODEL_PATH.exists():
        msg = f"Modelo de agente não encontrado em {settings.AGENTS_DIR}"
        logging.critical(msg)
        raise FileNotFoundError(msg)

    logging.info(f"Carregando modelo gerador: {settings.AGENT_MODEL_PATH.name}")
    try:
        llm = Llama(
            model_path=str(settings.AGENT_MODEL_PATH),
            n_ctx=settings.MAX_CONTEXT_LENGTH,
            n_gpu_layers=settings.N_GPU_LAYERS,
            n_threads=settings.N_THREADS,
            verbose=False
        )
        model_state["llm"] = llm
        logging.info(f"--- Serviço Gerador pronto na porta {settings.PORT} ---")
        yield
    except Exception as e:
        logging.critical(f"Erro ao carregar modelo gerador: {e}", exc_info=True)
        raise

    logging.info("--- Finalizando Serviço Gerador ---")
    model_state.clear()

app = FastAPI(lifespan=lifespan)

@app.post("/generate", response_model=GenerateResponse)
def generate_text(request: GenerateRequest):
    llm = model_state.get("llm")
    if not llm:
        raise HTTPException(status_code=503, detail="Modelo não inicializado.")

    try:
        logging.info(f"Recebida requisição de geração com prompt: '{request.prompt[:100]}...'")
        output = llm(
            request.prompt,
            max_tokens=1024,
            temperature=0.2,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["</s>", "[/INST]"]
        )
        response_text = output["choices"][0]["text"].strip()
        logging.info("Resposta gerada com sucesso.")
        return GenerateResponse(text=response_text)
    except Exception as e:
        logging.error(f"Erro na geração de texto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Falha ao gerar resposta.")

@app.get("/health")
def health_check():
    return {"status": "ok"}