FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY professionals.json .

ENV PYTHONPATH=/app

EXPOSE 8080

# Cloud Run always injects PORT=8080; shell form expands $PORT at runtime
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
