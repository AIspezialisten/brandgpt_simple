from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Ollama Configuration (running on host)
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="hf.co/Qwen/Qwen3-Embedding-8B-GGUF", env="OLLAMA_MODEL")
    ollama_llm_model: str = Field(default="mistral-small:24b", env="OLLAMA_LLM_MODEL")
    
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
    
    # Scrapy Configuration
    max_scrape_depth: int = Field(default=3, env="MAX_SCRAPE_DEPTH")
    concurrent_requests: int = Field(default=16, env="CONCURRENT_REQUESTS")
    download_delay: float = Field(default=0.5, env="DOWNLOAD_DELAY")
    
    # Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()