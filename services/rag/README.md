# Serviço RAG (Retrieval-Augmented Generation)

Este serviço é o orquestrador principal da aplicação de chatbot. Ele combina a recuperação de informações de uma base de conhecimento com a geração de texto para fornecer respostas relevantes e contextuais.

## Funcionalidades

- **Indexação de Documentos:** Na inicialização, o serviço lê documentos de vários formatos (txt, md, csv, pdf) do diretório `/data`, os divide em chunks e os indexa em um banco de dados vetorial (ChromaDB) usando o serviço de embedding.
- **Recuperação de Contexto:** Ao receber uma pergunta, ele a converte em um embedding e busca os chunks de texto mais relevantes no banco de dados vetorial.
- **Geração de Resposta:** Ele envia os chunks recuperados (contexto) e a pergunta original para o serviço gerador para criar uma resposta coesa e informativa.
- **Interface de Chat:** Expõe um endpoint `/chat` para interação com o usuário.

## Como Executar

O serviço é projetado para ser executado como um contêiner Docker e depende dos serviços de `embedding` e `generator`. Ele é iniciado pelo `docker-compose.yml` na raiz do projeto.

### Variáveis de Ambiente

- `EMBEDDING_SERVICE_URL`: URL do serviço de embedding.
- `GENERATOR_SERVICE_URL`: URL do serviço gerador.
- `CHUNK_SIZE`: Tamanho dos chunks de texto.
- `CHUNK_OVERLAP`: Sobreposição entre os chunks.
- `EMBEDDING_BATCH_SIZE`: Tamanho do lote para geração de embeddings.
- `TOP_K_RESULTS`: Número de chunks a serem recuperados do banco de dados vetorial.
- `COLLECTION_NAME`: Nome da coleção no ChromaDB.
- `RAG_PORT`: Porta em que o serviço será executado.

## Endpoint

### `POST /chat`

- **Requisição:**
  ```json
  {
    "pergunta": "Sua pergunta aqui"
  }
  ```
- **Resposta:**
  ```json
  {
    "resposta": "Resposta gerada pelo modelo, com base nos documentos encontrados."
  }
  ```
