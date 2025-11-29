FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for pdf2image and other packages
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.clean.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Cloud Run expects port 8080
ENV PORT=8080

# Run with uvicorn
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
