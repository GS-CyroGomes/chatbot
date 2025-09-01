# Guia de Configuração da GPU AMD (ROCm) para o Projeto

Este guia descreve como configurar seu ambiente para utilizar sua GPU AMD Radeon para acelerar os serviços de `embedding` e `generator` que usam `llama-cpp-python`.

## Passo 1: Pré-requisitos - Instalação do ROCm no Host

Antes de qualquer alteração no projeto, você **precisa** instalar a plataforma AMD ROCm em sua máquina host (seu sistema Linux). O ROCm é o conjunto de drivers e ferramentas da AMD que permite que aplicações, incluindo contêineres Docker, acessem e utilizem a GPU.

1.  **Siga o Guia Oficial da AMD:** A instalação varia de acordo com sua distribuição Linux (Ubuntu, CentOS, etc.). É crucial seguir o guia de instalação mais recente e apropriado para o seu sistema.
    *   [**Página de Instalação do AMD ROCm**](https://rocm.docs.amd.com/en/latest/deploy/linux/index.html)

2.  **Verifique a Instalação:** Após a instalação e uma reinicialização do sistema, execute o comando abaixo para garantir que a GPU está sendo reconhecida pelo ROCm:
    ```bash
    rocminfo
    ```
    Você deverá ver informações detalhadas sobre sua GPU AMD. Se este comando falhar, a configuração do Docker não funcionará.

## Passo 2: Modificar os Dockerfiles

Os `Dockerfile`s para os serviços `embedding` e `generator` precisam ser atualizados para que a biblioteca `llama-cpp-python` seja compilada com suporte para ROCm (via HIPBLAS).

**Aplique esta alteração em ambos os arquivos:**
- `services/embedding/Dockerfile`
- `services/generator/Dockerfile`

Localize a seção que instala as dependências do Python e a substitua.

**Substitua isto:**
```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt
```

**Por isto:**
```dockerfile
# Força a reinstalação do llama-cpp-python com suporte a ROCm (AMD GPU)
RUN pip install --no-cache-dir --upgrade pip && \
    CMAKE_ARGS="-DGGML_HIPBLAS=ON" pip install --no-cache-dir --force-reinstall -r /app/requirements.txt
```
*Esta alteração instrui o `pip` a reinstalar `llama-cpp-python` usando as flags `CMAKE_ARGS` que ativam a compilação com suporte a `HIPBLAS` (a interface da AMD análoga ao CUBLAS da Nvidia).*

## Passo 3: Modificar o `docker-compose.yml`

Agora, você precisa dar aos contêineres Docker acesso aos dispositivos da GPU no seu sistema host.

Edite o arquivo `docker-compose.yml` na raiz do projeto. Adicione a chave `devices` aos serviços `embedding` e `generator`:

```yaml
version: '3.8'

services:
  # ... (serviço de proxy sem alterações)

  embedding:
    build:
      context: ./services/embedding
    container_name: embedding-service
    env_file:
      - .env
    volumes:
      - ./models:/app/models
      - ./services/embedding/app/logs:/app/app/logs
    environment:
      - EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}
      - N_THREADS=${N_THREADS}
      - MAX_CONTEXT_LENGTH=${MAX_CONTEXT_LENGTH}
      - PORT=8000
    # --- Adicione as linhas abaixo ---
    devices:
      - /dev/kfd:/dev/kfd
      - /dev/dri:/dev/dri
    # ---------------------------------
    restart: unless-stopped

  generator:
    build:
      context: ./services/generator
    container_name: generator-service
    env_file:
      - .env
    volumes:
      - ./models:/app/models
      - ./services/generator/app/logs:/app/app/logs
    environment:
      - AGENT_MODEL_NAME=${AGENT_MODEL_NAME}
      - N_THREADS=${N_THREADS}
      - N_GPU_LAYERS=${N_GPU_LAYERS}
      - MAX_CONTEXT_LENGTH=${MAX_CONTEXT_LENGTH}
      - PORT=8000
    # --- Adicione as linhas abaixo ---
    devices:
      - /dev/kfd:/dev/kfd
      - /dev/dri:/dev/dri
    # ---------------------------------
    restart: unless-stopped

  # ... (serviço rag sem alterações)
```
*Os dispositivos `/dev/kfd` e `/dev/dri` são as interfaces que o ROCm usa para se comunicar com a GPU.*

## Passo 4: Reconstruir e Reiniciar os Serviços

Com as alterações salvas, siga os passos finais no seu terminal:

1.  **Reconstrua as imagens do Docker:** Este comando aplicará as alterações dos `Dockerfile`s, notavelmente a recompilação de `llama-cpp-python`.
    ```bash
    docker-compose build
    ```

2.  **Configure o Offload para a GPU:** Para que o modelo de linguagem realmente use a GPU, você precisa definir quantas camadas dele serão descarregadas para a VRAM. Edite seu arquivo `.env` e defina a variável `N_GPU_LAYERS`.
    ```
    # Exemplo no arquivo .env
    N_GPU_LAYERS=32
    ```
    Um bom ponto de partida é um número alto como `32` ou `64`. Se você encontrar erros de falta de memória (VRAM), diminua este valor. Se você definir como `0`, a GPU não será usada.

3.  **Inicie os serviços:**
    ```bash
    docker-compose up -d
    ```

4.  **Verifique os Logs:** Acompanhe os logs dos serviços `generator` ou `embedding` para ver se a GPU foi detectada e está sendo usada.
    ```bash
    docker logs -f generator-service
    ```
    Procure por mensagens de `llama.cpp` que mencionem `hip` ou `ROCm`, indicando que a aceleração por GPU está ativa.
