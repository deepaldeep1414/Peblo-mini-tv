FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port: defaults to 8088 locally; Render injects $PORT (10000 on free tier)
EXPOSE 8088

# Use shell form so $PORT is expanded at runtime
CMD sh -c "python -m seed.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8088}"
