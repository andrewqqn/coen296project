FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps for PDF / poppler / gcc
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ================================
# Final Image
# ================================
FROM python:3.11-slim

WORKDIR /app

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*


# Copy Python deps
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project — but we will delete .env and emulator configs immediately
COPY . .

# 🚨 Force remove any local dev configs accidentally copied into the image
RUN rm -f .env .env.* *.env \
    firebase.json \
    firestore.rules \
    firestore.indexes.json \
    google-services.json \
    **/*emulator* || true

RUN mkdir -p logs

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
