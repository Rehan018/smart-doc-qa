FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1+cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/start_api.sh scripts/start_worker.sh

EXPOSE 8000

CMD ["./scripts/start_api.sh"]
