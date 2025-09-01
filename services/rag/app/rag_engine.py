import time
import logging
import requests
from pathlib import Path
from typing import List, Tuple, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import count

import chromadb
from chromadb.config import Settings
from pypdf import PdfReader

from .config import settings

log = logging.getLogger(__name__)

# --- MÓDULO DE GERENCIAMENTO DE ARQUIVOS ---
class FileManager:
    @staticmethod
    def _read_txt_md_csv(file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            log.error(f"Falha ao ler o arquivo de texto {file_path}: {e}")
            return ""

    @staticmethod
    def _read_pdf(file_path: Path) -> str:
        try:
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        except Exception as e:
            log.error(f"Falha ao processar o arquivo PDF {file_path}: {e}")
            return ""

    @staticmethod
    def load_documents() -> List[Tuple[Path, str]]:
        all_files = []
        for dir_path in settings.FILE_PATHS:
            if not dir_path.exists():
                log.warning(f"Diretório não encontrado, pulando: {dir_path}")
                continue
            
            supported_extensions = ["*.txt", "*.md", "*.csv", "*.pdf"]
            for ext in supported_extensions:
                all_files.extend(list(dir_path.rglob(ext)))

        if not all_files:
            log.warning("Nenhum arquivo encontrado nos diretórios configurados.")
            return []
        
        log.info(f"Encontrados {len(all_files)} arquivos para processamento.")
        documents = []

        for file_path in all_files:
            content = ""
            if file_path.suffix in [".txt", ".md", ".csv"]:
                content = FileManager._read_txt_md_csv(file_path)
            elif file_path.suffix == ".pdf":
                content = FileManager._read_pdf(file_path)
            
            if content.strip():
                documents.append((file_path, content))
            else:
                log.warning(f"Arquivo {file_path} vazio ou não pôde ser lido, será ignorado.")
        return documents

    @staticmethod
    def chunk_text(text: str) -> List[str]:
        if not text: return []
        words = text.split()
        stride = settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
        chunks = [" ".join(words[i : i + settings.CHUNK_SIZE]) for i in range(0, len(words), stride)]
        return [chunk for chunk in chunks if chunk.strip()]

# --- CLIENTES HTTP PARA MICROSERVIÇOS ---
class EmbeddingClient:
    def __init__(self, service_url: str):
        self.service_url = service_url

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts: return []
        try:
            response = requests.post(self.service_url, json={"texts": texts}, timeout=90)
            response.raise_for_status()
            return response.json()["embeddings"]
        except requests.exceptions.RequestException as e:
            log.error(f"Falha ao contatar o serviço de embedding em {self.service_url}: {e}")
            return [[] for _ in texts]

class GeneratorClient:
    def __init__(self, service_url: str):
        self.service_url = service_url
    
    def chat(self, user_prompt: str) -> str:
        prompt = f"<s>[INST] <<SYS>>\n{settings.RAG_SYSTEM_PROMPT}\n<</SYS>>\n\n{user_prompt} [/INST]"
        try:
            response = requests.post(self.service_url, json={"prompt": prompt}, timeout=6000)
            response.raise_for_status()
            return response.json()["text"]
        except requests.exceptions.RequestException as e:
            log.error(f"Falha ao contatar o serviço gerador em {self.service_url}: {e}")
            return "Desculpe, ocorreu um erro de comunicação ao tentar gerar a resposta."

# --- VECTOR STORE ---
class ChromaStore:
    def __init__(self):
        settings.DB_DIR.mkdir(exist_ok=True)
        self.client = chromadb.Client(
            Settings(is_persistent=True, persist_directory=str(settings.DB_DIR))
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        log.info(f"Vector store '{settings.COLLECTION_NAME}' conectado em {settings.DB_DIR}.")

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: List[str]):
        if not ids: return
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    def query(self, query_embedding: List[float]) -> Tuple[List[str], List[str]]:
        res = self.collection.query(query_embeddings=[query_embedding], n_results=settings.TOP_K_RESULTS)
        docs = res.get("documents", [[]])[0]
        sources = [m.get("source", "?") for m in res.get("metadatas", [[]])[0]]
        return docs, sources

# --- WORKER PARA MULTIPROCESSING ---
doc_id_counter = count()

def process_file_to_chunks(file_content_tuple: Tuple[Path, str]) -> List[Tuple[str, dict]]:
    file_path, content = file_content_tuple
    chunks = FileManager.chunk_text(content)
    return [(chunk, {"source": str(file_path.name)}) for chunk in chunks]

# --- PIPELINE PRINCIPAL ---
class RAGPipeline:
    def __init__(self, embedder: EmbeddingClient, store: ChromaStore, generator: GeneratorClient):
        self.embedder = embedder
        self.store = store
        self.generator = generator

    def build_index(self):
        log.info("Iniciando construção do índice...")
        start_time = time.time()
        
        documents = FileManager.load_documents()
        if not documents:
            log.info("Nenhum documento novo para indexar.")
            return

        all_chunks_with_meta = []
        with ProcessPoolExecutor(max_workers=settings.N_THREADS) as executor:
            futures = [executor.submit(process_file_to_chunks, doc) for doc in documents]
            for future in as_completed(futures):
                all_chunks_with_meta.extend(future.result())

        if not all_chunks_with_meta:
            log.warning("Nenhum chunk gerado. Índice não foi modificado.")
            return

        log.info(f"Total de {len(all_chunks_with_meta)} chunks gerados. Criando embeddings em lotes...")
        
        chunks_to_embed = [c[0] for c in all_chunks_with_meta]
        all_embeddings = []
        for i in range(0, len(chunks_to_embed), settings.EMBEDDING_BATCH_SIZE):
            batch_chunks = chunks_to_embed[i : i + settings.EMBEDDING_BATCH_SIZE]
            batch_embeddings = self.embedder.embed(batch_chunks)
            all_embeddings.extend(batch_embeddings)
            log.info(f"Processado lote de embeddings {i // settings.EMBEDDING_BATCH_SIZE + 1}...")

        ids = [f"doc_{next(doc_id_counter)}" for _ in all_chunks_with_meta]
        metadatas = [c[1] for c in all_chunks_with_meta]
        
        self.store.add(ids, all_embeddings, metadatas, chunks_to_embed)
        
        end_time = time.time()
        log.info(f"Índice construído com sucesso em {end_time - start_time:.2f} segundos.")

    def query(self, pergunta: str) -> str:
        log.info(f"Recebida nova pergunta: '{pergunta[:80]}...'")
        query_embedding = self.embedder.embed([pergunta])[0]
        
        if not query_embedding:
            return "Não foi possível processar a pergunta. Verifique o serviço de embedding."

        contexts, sources = self.store.query(query_embedding)

        if not contexts:
            return "Não encontrei informações relevantes nas fontes para responder a sua pergunta."

        context_str = "\n\n---\n\n".join(contexts)
        user_prompt = f"CONTEXTO:\n{context_str}\n\nPERGUNTA:\n{pergunta}\n\nResponda de forma concisa."
        
        reply = self.generator.chat(user_prompt)
        unique_sources = "\n".join(f"- {s}" for s in sorted(set(sources)))
        return f"{reply}\n\n**Fontes:**\n{unique_sources}"