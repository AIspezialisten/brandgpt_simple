from typing import List
from langchain_ollama import OllamaEmbeddings
from brandgpt.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        # Configure longer timeouts for the Ollama client
        # The default timeout in ollama/httpx is often 120 seconds,
        # but embedding generation for large batches can take longer
        from httpx import Timeout

        # We use async methods (aembed_documents), so configure async_client_kwargs
        timeout_config = Timeout(300.0)  # 5 minutes timeout for HTTP requests

        self.embeddings = OllamaEmbeddings(
            base_url=settings.ollama_embedding_url,
            model=settings.ollama_embedding_model,
            keep_alive=settings.ollama_keep_alive,
            async_client_kwargs={"timeout": timeout_config},
            sync_client_kwargs={"timeout": timeout_config}  # Also set for sync, just in case
        )
        logger.info(f"EmbeddingService initialized with URL: {settings.ollama_embedding_url}, Model: {settings.ollama_embedding_model}, Timeout: 300s")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with timeout and batch processing.

        For large batches (>50 texts), processes in smaller batches to avoid timeouts.
        Each batch has a 300-second timeout.
        """
        try:
            # For small batches, process normally
            if len(texts) <= 50:
                logger.info(f"Generating embeddings for {len(texts)} documents")
                embeddings = await asyncio.wait_for(
                    self.embeddings.aembed_documents(texts),
                    timeout=300.0  # 5 minutes timeout
                )
                logger.info(f"✅ Generated embeddings for {len(texts)} documents")
                return embeddings

            # For large batches, process in chunks
            logger.info(f"Processing {len(texts)} documents in batches of 50")
            all_embeddings = []
            batch_size = 50

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(texts) + batch_size - 1) // batch_size

                logger.info(f"Processing embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")

                try:
                    batch_embeddings = await asyncio.wait_for(
                        self.embeddings.aembed_documents(batch),
                        timeout=300.0  # 5 minutes per batch
                    )
                    all_embeddings.extend(batch_embeddings)
                    logger.info(f"✅ Batch {batch_num}/{total_batches} completed")

                    # Small pause between batches
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.5)

                except asyncio.TimeoutError:
                    logger.error(f"❌ Embedding batch {batch_num}/{total_batches} timed out after 300s")
                    raise TimeoutError(f"Embedding generation timed out for batch {batch_num}/{total_batches}")
                except Exception as batch_error:
                    logger.error(f"❌ Error in batch {batch_num}/{total_batches}: {str(batch_error)}")
                    raise

            logger.info(f"✅ Generated embeddings for all {len(texts)} documents")
            return all_embeddings

        except asyncio.TimeoutError:
            logger.error(f"❌ Embedding generation timed out for {len(texts)} documents")
            raise TimeoutError(f"Embedding generation timed out after 300 seconds")
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {str(e)}")
            raise
    
    async def embed_query(self, text: str) -> List[float]:
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise