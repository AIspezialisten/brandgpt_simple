# BrandGPT Simple

A RAG (Retrieval-Augmented Generation) application built with LangGraph, LangChain, and FastAPI.

## Features

- **Multi-format Ingestion**: Process PDFs, text files, JSON, and URLs
- **Vector Storage**: Qdrant integration with high-dimensional embeddings
- **Advanced RAG Pipeline**: LangGraph workflow with retrieval, reranking, and generation
- **Authentication**: Session-based API with OAuth2
- **Prompt Management**: Store and reuse system prompts
- **Web Scraping**: Configurable depth URL crawling with Scrapy

## Prerequisites

- Python 3.11+ (for development)
- Docker and Docker Compose (for deployment)
- Ollama running on host system (http://localhost:11434)
- SQLite (included with Python)

## Quick Start (Docker Deployment)

1. **Setup Ollama on Host** (required):
```bash
# Install Ollama on your host system
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
ollama pull mistral-small:24b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

2. **Deploy with Docker**:
```bash
git clone <repository-url>
cd brandgpt_simple

# Create data directory
mkdir -p data

# Deploy services
docker-compose up -d

# Check status
docker-compose ps
```

3. **Access the Application**:
- API: http://localhost:9700
- Documentation: http://localhost:9700/docs
- Health Check: http://localhost:9700/health

## Development Setup

For local development without Docker:

```bash
# Install dependencies
uv pip install -e .

# Copy environment file
cp .env.example .env

# Start development server
uv run python main.py
```

## API Workflow

1. **Register a user**: POST `/api/auth/register`
2. **Login**: POST `/api/auth/token`
3. **Create a session**: POST `/api/sessions`
4. **Ingest documents**: 
   - POST `/api/ingest/file` for PDFs/text/JSON
   - POST `/api/ingest/url` for web pages
5. **Query**: POST `/api/query`

## Configuration

Key environment variables (see `.env.example`):

- `OLLAMA_BASE_URL`: Ollama server URL
- `QDRANT_URL`: Qdrant server URL
- `CHUNK_SIZE`: Text chunk size for processing
- `RERANKER_TOP_K`: Number of documents after reranking
- `MAX_SCRAPE_DEPTH`: Maximum depth for URL crawling

## Architecture

The application uses:
- **LangGraph** for orchestrating the RAG pipeline
- **LangChain** for document processing and LLM integration
- **Qdrant** for vector storage
- **Ollama** for embeddings and LLM inference
- **FastAPI** for the REST API
- **SQLite** for metadata storage

## Testing

The application includes a comprehensive test suite covering:

### Test Categories
- **Authentication Tests**: User registration, login, token validation
- **Ingestion Tests**: PDF, text, JSON, and URL processing
- **Query Tests**: RAG pipeline, retrieval, reranking, and response generation
- **Integration Tests**: Complete end-to-end workflows
- **Performance Tests**: Load testing and response time validation

### Running Tests

```bash
# Install test dependencies
uv pip install -e .

# Run all unit tests
uv run pytest tests/ -v

# Run specific test categories
python run_tests.py --suite auth        # Authentication tests
python run_tests.py --suite ingestion   # Document ingestion tests
python run_tests.py --suite query       # Query and RAG tests
python run_tests.py --suite integration # Full pipeline tests
python run_tests.py --suite performance # Performance tests (slow)

# Quick test run (skip slow tests)
python run_tests.py --suite all --fast

# Run tests in parallel
python run_tests.py --suite all --parallel
```

### Test Requirements
- All external dependencies (Ollama, Qdrant) should be running for integration tests
- Some tests create temporary files and mock servers
- Performance tests may take several minutes to complete

## Deployment

For detailed production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Development

See the testing section above for development workflows.

## License

MIT