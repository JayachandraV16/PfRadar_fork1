FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    gcc \
    build-essential \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
