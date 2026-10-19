# API del notebook (api.py) en un contenedor, como Ollama: Docker la reinicia sola en cada arranque.
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api.py prompts.py ./
# Caché de Hugging Face en el disco persistente (se monta en /hf)
ENV HF_HOME=/hf
CMD ["uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"]
