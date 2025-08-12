from typing import List
from langchain_ollama import OllamaEmbeddings
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            logger.info(f"Generated embeddings for {len(texts)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def embed_query(self, text: str) -> List[float]:
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise