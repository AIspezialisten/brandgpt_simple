FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

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

# Run the application
CMD ["python", "main.py"]