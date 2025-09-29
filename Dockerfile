# Multi-stage build: Stage 1 - Pre-pull Ollama models
FROM ollama/ollama:latest as ollama-models

# Pull required models
RUN ollama serve & \
    sleep 10 && \
    ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF && \
    ollama pull mistral-small:24b && \
    sleep 5 && \
    pkill ollama

# Stage 2 - BrandGPT application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including OpenGL libraries, poppler, and tesseract for PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    libsm6 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-pulled Ollama models from first stage
COPY --from=ollama-models /root/.ollama /root/.ollama

# Install uv
RUN pip install uv

# Copy all necessary files
COPY pyproject.toml ./
COPY README.md ./
COPY brandgpt/ ./brandgpt/
COPY main.py ./

# Install dependencies and package
RUN uv pip install --system .

# Copy environment template
COPY .env.example ./.env

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 9700

# Healthcheck to ensure both app and required models are available
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9700/health || exit 1

# Run the application
CMD ["python", "main.py"]