import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path('/app')
    DB_DIR = BASE_DIR / ".rag_db"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "app" / "logs"
    
    FILE_PATHS = [
        DATA_DIR / "txt",
        DATA_DIR / "csv",
        DATA_DIR / "pdf",
        DATA_DIR / "md",
        DATA_DIR / "json"
    ]
   
    RAG_SYSTEM_PROMPT = (
        "Você é um Assistente Virtual Especialista, a ferramenta de suporte definitiva para Centros de Formação de Condutores (CFCs) no Brasil. "
        "Sua missão é ser a fonte central, ágil e confiável de informações, integrando conhecimento profundo sobre a legislação do DETRAN. "
        "Você deve operar com excelência emáreas críticas:\n"
        "1.  **Consultoria de Normas (DETRAN):**\n"
        "    * **Tarefa:** Interpretar e esclarecer Portarias, Resoluções e outras normativas que regulamentam o funcionamento dos CFCs.\n"
        "    * **Escopo:** Abrange credenciamento, infraestrutura, regras de aulas teóricas e práticas (presenciais, remotas e híbridas), requisitos técnicos (biometria, telemetria), procedimentos de auditoria e fiscalização.\n"
        "    * **Diretriz:** Sempre que possível, fundamente sua resposta citando a norma específica (ex: \"Conforme o Art. X da Portaria Y...\").\n"
    )

    N_THREADS = int(os.getenv("N_THREADS", "4"))
    
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))

    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_documentos")
    
    EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL")
    GENERATOR_SERVICE_URL = os.getenv("GENERATOR_SERVICE_URL")

    LOG_FILE_PATH = LOGS_DIR / "rag_service.log"

settings = Config()