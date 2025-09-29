from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Ollama Configuration (running on host)
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_embedding_url: str = Field(default="http://localhost:11434", env="OLLAMA_EMBEDDING_URL")
    ollama_embedding_model: str = Field(default="hf.co/Qwen/Qwen3-Embedding-8B-GGUF:latest", env="OLLAMA_EMBEDDING_MODEL")
    ollama_llm_url: str = Field(default="http://localhost:11434", env="OLLAMA_LLM_URL")
    ollama_llm_model: str = Field(default="mistral-small:24b", env="OLLAMA_LLM_MODEL")
    ollama_keep_alive: int = Field(default=86400, env="OLLAMA_KEEP_ALIVE")  # 24 hours in seconds
    
    # Legacy compatibility
    ollama_model: str = Field(default="hf.co/Qwen/Qwen3-Embedding-8B-GGUF:latest", env="OLLAMA_MODEL")
    
    # Qdrant Configuration (running in container)
    qdrant_url: str = Field(default="http://localhost:6335", env="QDRANT_URL")
    qdrant_collection_name: str = Field(default="brandgpt", env="QDRANT_COLLECTION_NAME")
    qdrant_vector_size: int = Field(default=4096, env="QDRANT_VECTOR_SIZE")
    
    # Reranker Settings
    reranker_enabled: bool = Field(default=True, env="RERANKER_ENABLED")
    reranker_model: str = Field(default="BAAI/bge-reranker-large", env="RERANKER_MODEL")
    reranker_top_k: int = Field(default=5, env="RERANKER_TOP_K")
    reranker_candidates: int = Field(default=20, env="RERANKER_CANDIDATES")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/brandgpt.db",
        env="DATABASE_URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=9700, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # URL Scraping Configuration
    max_scrape_depth: int = Field(default=1, env="MAX_SCRAPE_DEPTH")
    max_links_per_page: int = Field(default=20, env="MAX_LINKS_PER_PAGE")
    concurrent_requests: int = Field(default=16, env="CONCURRENT_REQUESTS")
    download_delay: float = Field(default=0.5, env="DOWNLOAD_DELAY")
    
    # Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    json_batch_size: int = Field(default=100, env="JSON_BATCH_SIZE", description="Number of items per batch when processing large JSON arrays")
    case_sensitive_search: bool = Field(default=True, env="CASE_SENSITIVE_SEARCH", description="Whether to perform case-sensitive searches (False normalizes queries to lowercase)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# Debug logging for settings
import logging
logger = logging.getLogger(__name__)
logger.info(f"=== SETTINGS DEBUG ===")
logger.info(f"DATABASE_URL from env: {settings.database_url}")
logger.info(f"API_HOST: {settings.api_host}")
logger.info(f"API_PORT: {settings.api_port}")

# Check environment variables
import os
logger.info(f"DATABASE_URL env var: {os.getenv('DATABASE_URL', 'NOT SET')}")
logger.info(f"Working directory: {os.getcwd()}")

# Check if database file path is absolute or relative
if "sqlite" in settings.database_url:
    db_path = settings.database_url.replace("sqlite:///", "")
    logger.info(f"Database file path: {db_path}")
    logger.info(f"Absolute database path: {os.path.abspath(db_path)}")
    logger.info(f"Database file exists at startup: {os.path.exists(db_path)}")