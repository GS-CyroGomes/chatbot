import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .rag_engine import RAGPipeline, EmbeddingClient, ChromaStore, GeneratorClient
from .models import ChatRequest, ChatResponse
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

pipeline_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):   
    logging.info("--- Iniciando Servidor RAG Orquestrador ---")
    
    if not all([settings.EMBEDDING_SERVICE_URL, settings.GENERATOR_SERVICE_URL]):
        msg = "URLs dos serviços de embedding e/ou gerador não foram configuradas no ambiente."
        logging.critical(msg)
        raise ValueError(msg)

    try:
        embedder_client = EmbeddingClient(service_url=settings.EMBEDDING_SERVICE_URL)
        generator_client = GeneratorClient(service_url=settings.GENERATOR_SERVICE_URL)
        store = ChromaStore()
        
        pipeline = RAGPipeline(embedder=embedder_client, store=store, generator=generator_client)
        
        logging.info("Construindo índice de embeddings. O servidor ficará disponível após o término...")
        pipeline.build_index()
        logging.info("Índice de embeddings concluído.")

        pipeline_state["rag_pipeline"] = pipeline
        logging.info("--- Servidor RAG pronto para receber requisições ---")

    except Exception as e:
        logging.critical(f"Erro inesperado durante a inicialização do orquestrador: {e}", exc_info=True)
        raise

    yield

    logging.info("--- Finalizando Servidor RAG Orquestrador ---")
    pipeline_state.clear()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "Servidor RAG Orquestrador online."}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    pipeline = pipeline_state.get("rag_pipeline")
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline RAG não está inicializado.")

    if not request.pergunta:
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")

    try:
        resposta = pipeline.query(request.pergunta)
        return ChatResponse(resposta=resposta)
    except Exception as e:
        logging.error(f"Erro ao processar a pergunta: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao processar sua pergunta.")

@app.get("/health")
def health_check():
    return {"status": "ok"}