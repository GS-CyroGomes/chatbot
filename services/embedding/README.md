# Serviço de Embedding

Este serviço é responsável por gerar embeddings para textos. Ele utiliza um modelo de linguagem GGUF para transformar textos em vetores numéricos.

## Funcionalidades

- Expõe um endpoint `/embed` que aceita uma lista de textos e retorna seus embeddings correspondentes.
- Carrega um modelo de embedding no formato GGUF.
- Utiliza a biblioteca `llama-cpp-python` para interagir com o modelo.

## Como Executar

O serviço é projetado para ser executado como um contêiner Docker. Ele é iniciado pelo `docker-compose.yml` na raiz do projeto.

### Variáveis de Ambiente

- `EMBEDDING_MODEL_NAME`: O nome do arquivo do modelo de embedding a ser usado (sem o caminho completo).
- `N_THREADS`: Número de threads para o modelo.
- `MAX_CONTEXT_LENGTH`: Comprimento máximo do contexto para o modelo.
- `EMBEDDING_PORT`: Porta em que o serviço será executado.

## Endpoint

### `POST /embed`

- **Requisição:**
  ```json
  {
    "texts": ["texto 1", "texto 2"]
  }
  ```
- **Resposta:**
  ```json
  {
    "embeddings": [
      [0.1, 0.2, ...],
      [0.3, 0.4, ...]
    ]
  }
  ```
