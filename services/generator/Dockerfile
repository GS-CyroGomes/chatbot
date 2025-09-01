FROM python:3.11-slim

WORKDIR /app

# instala dependências de compilação necessárias para llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    CMAKE_ARGS="-DGGML_HIPBLAS=ON" pip install --no-cache-dir --force-reinstall -r /app/requirements.txt

COPY ./app /app/app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]