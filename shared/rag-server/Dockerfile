FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/chroma && useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app

# Mount persistent storage at /app/chroma in Azure Container Apps.
USER appuser

EXPOSE 7002

CMD ["python", "-u", "rag_http_server.py"]
