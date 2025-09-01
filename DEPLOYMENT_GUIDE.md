# Guia de Implantação Distribuída com Docker Swarm

Este guia detalha o processo para implantar a aplicação de chatbot RAG em um ambiente distribuído, utilizando múltiplas máquinas (nós) gerenciadas pelo Docker Swarm. Esta abordagem permite escalar os serviços individualmente e aumentar a resiliência da aplicação.

## Arquitetura da Solução

A aplicação consiste em três serviços principais:
1.  `embedding-service`: Converte texto em vetores numéricos (embeddings).
2.  `generator-service`: Gera respostas em linguagem natural.
3.  `rag-orchestrator`: Orquestra a lógica de RAG, consultando os outros dois serviços.

Para a implantação distribuída, usaremos:
- **Docker Swarm:** Para orquestrar os contêineres em um cluster de máquinas.
- **Container Registry:** Um repositório central (como Docker Hub, AWS ECR, Google GCR) para armazenar e distribuir as imagens Docker para os nós do cluster.

---

## Passo a Passo para Implantação

### Pré-requisitos

1.  **Múltiplas Máquinas (Nós):** Pelo menos duas máquinas (físicas ou virtuais) com Linux e conectividade de rede entre elas. Uma será o "Manager" e as outras serão "Workers".
2.  **Docker Instalado:** O Docker deve estar instalado em **todas** as máquinas do cluster.
3.  **Conta em um Container Registry:** Você precisará de uma conta em um serviço como o [Docker Hub](https://hub.docker.com/) para hospedar suas imagens.

---

### Passo 1: Configurar o Cluster Docker Swarm

O Docker Swarm agrupa várias máquinas Docker em um único "enxame" virtual.

1.  **Escolha o Nó Manager:**
    Acesse via SSH a máquina que você designou como o nó principal (Manager).

2.  **Inicialize o Swarm:**
    Execute o seguinte comando no nó Manager. Ele o tornará o líder do cluster.

    ```bash
    docker swarm init --advertise-addr <IP_DO_MANAGER>
    ```
    - Substitua `<IP_DO_MANAGER>` pelo endereço IP da máquina Manager (ex: `192.168.1.10`).

3.  **Obtenha o Comando para Adicionar Workers:**
    Após a execução, o comando acima irá gerar uma saída contendo o token e o comando para que outros nós se juntem ao swarm. Se parece com isto:

    ```
    docker swarm join --token SWMTKN-1-xxxxxxxx... <IP_DO_MANAGER>:2377
    ```
    **Guarde este comando.** Se você o perder, pode recuperá-lo executando `docker swarm join-token worker` no Manager.

4.  **Adicione os Nós Workers:**
    Acesse via SSH cada uma das outras máquinas (Workers) e execute o comando `docker swarm join...` que você guardou.

5.  **Verifique o Cluster:**
    De volta ao nó Manager, execute o comando abaixo para listar todos os nós e verificar se o cluster foi formado com sucesso:

    ```bash
    docker node ls
    ```
    Você deverá ver todos os seus nós (Manager e Workers) com o status `Ready`.

---

### Passo 2: Construir e Publicar as Imagens Docker

Para que os nós Workers possam executar seus serviços, as imagens Docker precisam estar em um registro central que todos possam acessar.

1.  **Faça Login no seu Registry:**
    Na sua máquina local (ou no nó Manager, onde o código-fonte está), faça login no seu registro. Para o Docker Hub:

    ```bash
    docker login -u SEU_USUARIO_DOCKER_HUB
    ```

2.  **Construa e Tagueie as Imagens:**
    Para cada serviço (`embedding`, `generator`, `rag`), você precisa construir a imagem e tagueá-la com o nome do seu usuário/organização no registro.

    ```bash
    # Navegue até a raiz do projeto
    cd /caminho/para/chatbot

    # Imagem do Embedding Service
    docker build -t SEU_USUARIO_DOCKER_HUB/embedding-service:latest -f services/embedding/Dockerfile .

    # Imagem do Generator Service
    docker build -t SEU_USUARIO_DOCKER_HUB/generator-service:latest -f services/generator/Dockerfile .

    # Imagem do RAG Service
    docker build -t SEU_USUARIO_DOCKER_HUB/rag-service:latest -f services/rag/Dockerfile .
    ```
    > **Importante:** Substitua `SEU_USUARIO_DOCKER_HUB` pelo seu nome de usuário real.

3.  **Publique as Imagens (Push):**
    Agora, envie as imagens tagueadas para o registro.

    ```bash
    docker push SEU_USUARIO_DOCKER_HUB/embedding-service:latest
    docker push SEU_USUARIO_DOCKER_HUB/generator-service:latest
    docker push SEU_USUARIO_DOCKER_HUB/rag-service:latest
    ```

---

### Passo 3: Adaptar o `docker-compose.yml` para Deploy em Stack

O Docker Swarm usa um conceito de "Stack" que é muito similar ao `docker-compose`, mas com algumas adaptações para ambientes distribuídos.

Crie um novo arquivo chamado `docker-stack.yml` (ou modifique o `docker-compose.yml`) com o seguinte conteúdo:

```yaml
version: '3.8'

services:
  embedding:
    image: SEU_USUARIO_DOCKER_HUB/embedding-service:latest # Alterado de 'build' para 'image'
    env_file:
      - .env
    volumes:
      - /path/nas/maquinas/models:/app/models # Caminho absoluto nos nós
      - /path/nas/maquinas/logs/embedding:/app/app/logs # Caminho absoluto nos nós
    environment:
      - EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}
      - N_THREADS=${N_THREADS}
      - MAX_CONTEXT_LENGTH=${MAX_CONTEXT_LENGTH}
      - PORT=8001 # A porta interna do contêiner
    deploy:
      replicas: 1 # Quantas instâncias deste serviço você quer
      placement:
        constraints: [node.role == worker] # Onde executar (ex: apenas em workers)

  generator:
    image: SEU_USUARIO_DOCKER_HUB/generator-service:latest # Alterado
    env_file:
      - .env
    volumes:
      - /path/nas/maquinas/models:/app/models # Caminho absoluto nos nós
      - /path/nas/maquinas/logs/generator:/app/app/logs # Caminho absoluto nos nós
    environment:
      - AGENT_MODEL_NAME=${AGENT_MODEL_NAME}
      - N_THREADS=${N_THREADS}
      - N_GPU_LAYERS=${N_GPU_LAYERS}
      - MAX_CONTEXT_LENGTH=${MAX_CONTEXT_LENGTH}
      - PORT=8002 # A porta interna do contêiner
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == worker]

  rag:
    image: SEU_USUARIO_DOCKER_HUB/rag-service:latest # Alterado
    ports:
      - "8000:8000" # Expõe a porta 8000 do RAG para o mundo exterior
    env_file:
      - .env
    volumes:
      - /path/nas/maquinas/data:/app/data # Caminho absoluto nos nós
      - /path/nas/maquinas/rag_db:/app/.rag_db # Caminho absoluto nos nós
      - /path/nas/maquinas/logs/rag:/app/app/logs # Caminho absoluto nos nós
    depends_on:
      - embedding
      - generator
    environment:
      # O Docker Swarm usa o nome do serviço para DNS discovery
      - EMBEDDING_SERVICE_URL=http://embedding:8001/embed
      - GENERATOR_SERVICE_URL=http://generator:8002/generate
      - CHUNK_SIZE=${CHUNK_SIZE}
      - CHUNK_OVERLAP=${CHUNK_OVERLAP}
      - EMBEDDING_BATCH_SIZE=${EMBEDDING_BATCH_SIZE}
      - TOP_K_RESULTS=${TOP_K_RESULTS}
      - COLLECTION_NAME=${COLLECTION_NAME}
      - N_THREADS=${N_THREADS}
      - PORT=8000
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager] # Ex: executar o orquestrador no manager
```

**Ajustes Críticos no `docker-stack.yml`:**
1.  **`image`:** Substitua os blocos `build` por `image`, apontando para as imagens que você publicou no registro.
2.  **`volumes`:** Os caminhos dos volumes devem ser **caminhos absolutos** que existam em **todas as máquinas** (nós) onde o serviço pode ser executado. Use um sistema de arquivos de rede (NFS) ou certifique-se de que os diretórios (`models`, `data`, `.rag_db`) estejam presentes e sincronizados em todos os nós relevantes.
3.  **`ports`:** Exponha apenas a porta do serviço principal que precisa ser acessado externamente (neste caso, o `rag-orchestrator` na porta `8000`). Os serviços se comunicarão internamente pela rede overlay do Swarm.
4.  **`deploy`:** Esta chave é específica do Swarm e permite definir o número de réplicas, restrições de posicionamento (`placement`), políticas de atualização e limites de recursos.

---

### Passo 4: Implantar a Stack no Cluster

Com o arquivo `docker-stack.yml` e o `.env` prontos no nó Manager:

1.  **Execute o Deploy:**
    No nó Manager, execute o comando:

    ```bash
    docker stack deploy -c docker-stack.yml nome_da_sua_stack
    ```
    - Substitua `nome_da_sua_stack` por um nome para sua aplicação (ex: `chatbot-rag`).

2.  **Verifique o Status dos Serviços:**
    O Docker Swarm começará a baixar as imagens nos nós e a iniciar os contêineres. Você pode monitorar o progresso com:

    ```bash
    docker service ls
    ```
    Espere até que a coluna `REPLICAS` mostre `1/1` para todos os serviços.

3.  **Verifique os Logs (se necessário):**
    Se um serviço não iniciar, você pode ver seus logs com:

    ```bash
    docker service logs nome_da_sua_stack_nome_do_servico
    ```
    Exemplo: `docker service logs chatbot-rag_rag`

---

### Passo 5: Acessar e Usar a Aplicação

Uma vez que todos os serviços estejam rodando, a aplicação estará acessível através da porta que você publicou (`8000`) em **qualquer nó** do cluster, graças à rede de roteamento do Swarm.

Você pode enviar uma requisição para o IP de qualquer máquina do cluster:

```bash
curl -X POST "http://<IP_DE_QUALQUER_NO_DO_SWARM>:8000/chat" -H "Content-Type: application/json" -d '{
  "pergunta": "Qual o procedimento para renovação da CNH?"
}'
```

O Swarm irá rotear a requisição automaticamente para o contêiner do serviço `rag` que estiver em execução, não importa em qual nó ele esteja.
