FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full application
COPY . .

ENV PYTHONPATH=/app

EXPOSE 8080

# Cloud Run injects PORT=8080 at runtime; shell form expands $PORT
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
