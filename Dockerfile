# --- Base image ---
FROM python:3.11-slim

# --- Set workdir ---
WORKDIR /app

# --- Copy files ---
COPY requirements.txt .
COPY app.py .

# --- Install dependencies ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Expose port ---
EXPOSE 3333

# --- Command to run ---
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3333", "--loop", "asyncio", "--http", "h11"]
