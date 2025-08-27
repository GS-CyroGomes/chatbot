# Chatbot com RAG (Retrieval-Augmented Generation)

Este projeto implementa um chatbot que utiliza a arquitetura RAG para responder a perguntas com base em um conjunto de documentos. A solução é dividida em três serviços containerizados: um para geração de embeddings, um para geração de texto e um orquestrador RAG.

## Arquitetura

A aplicação é composta pelos seguintes serviços:

- **Serviço de Embedding:** Responsável por converter textos em representações numéricas (embeddings) utilizando um modelo de linguagem.
- **Serviço Gerador:** Responsável por gerar texto a partir de um prompt utilizando um modelo de linguagem.
- **Serviço RAG:** O orquestrador que recebe as perguntas dos usuários, busca informações relevantes nos documentos previamente indexados e utiliza o serviço gerador para criar uma resposta.

## Como Executar o Projeto

### Pré-requisitos

- Docker
- Docker Compose

### Passos

1. **Clone o repositório:**
   ```bash
   git clone git@github.com:GS-CyroGomes/chatbot.git
   cd chatbot
   ```

2. **Configure as variáveis de ambiente:**
   - Renomeie o arquivo `.env.example` para `.env`.
   - Edite o arquivo `.env` com as configurações desejadas (portas, nomes dos modelos, etc.).

3. **Adicione seus documentos:**
   - Coloque os arquivos que servirão como base de conhecimento nos diretórios apropriados dentro de `data/` (txt, pdf, etc.).

4. **Adicione os modelos:**
   - Coloque os modelos GGUF nos diretórios `models/embeddings` e `models/agents` conforme especificado no arquivo `.env`.

5. **Inicie os serviços:**
   ```bash
   docker-compose up -d
   ```
   O serviço RAG irá iniciar a indexação dos documentos, o que pode levar algum tempo dependendo do volume de dados.

## Como Consumir

Após a inicialização dos contêineres, você pode interagir com o chatbot enviando requisições para o endpoint `/chat` do serviço RAG.

### Exemplo de Requisição

```bash
curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d '{
  "pergunta": "Qual o procedimento para renovação da CNH?"
}'
```

### Resposta Esperada

```json
{
  "resposta": "A resposta para sua pergunta, gerada com base nos documentos fornecidos."
}
```

## Serviços

Para mais detalhes sobre cada serviço, consulte os arquivos `README.md` em seus respectivos diretórios:

- [[services/embedding/README|Embedding]]
- [[services/generator/README|Generator]]
- [[services/rag/README|Rag]]
