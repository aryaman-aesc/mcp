FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Render expects $PORT
EXPOSE 10000

CMD ["uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "10000", \
     "--workers", "1", \
     "--loop", "asyncio", \
     "--http", "h11", \
     "--timeout-keep-alive", "0", \
     "--log-level", "info"]
