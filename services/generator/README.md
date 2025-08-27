# Serviço Gerador

Este serviço é responsável por gerar texto a partir de um prompt. Ele utiliza um modelo de linguagem GGUF para gerar respostas.

## Funcionalidades

- Expõe um endpoint `/generate` que aceita um prompt e retorna o texto gerado.
- Carrega um modelo de geração no formato GGUF.
- Utiliza a biblioteca `llama-cpp-python` para interagir com o modelo.

## Como Executar

O serviço é projetado para ser executado como um contêiner Docker. Ele é iniciado pelo `docker-compose.yml` na raiz do projeto.

### Variáveis de Ambiente

- `AGENT_MODEL_NAME`: O nome do arquivo do modelo de agente a ser usado (sem o caminho completo).
- `N_THREADS`: Número de threads para o modelo.
- `N_GPU_LAYERS`: Número de camadas a serem descarregadas na GPU.
- `MAX_CONTEXT_LENGTH`: Comprimento máximo do contexto para o modelo.
- `GENERATOR_PORT`: Porta em que o serviço será executado.

## Endpoint

### `POST /generate`

- **Requisição:**
  ```json
  {
    "prompt": "Seu prompt aqui"
  }
  ```
- **Resposta:**
  ```json
  {
    "text": "Texto gerado"
  }
  ```
