from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Modelo para a requisição de chat."""
    pergunta: str

class ChatResponse(BaseModel):
    """Modelo para a resposta do chat."""
    resposta: str