from typing import List
from langchain_ollama import OllamaEmbeddings
from brandgpt.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        # Configure longer timeouts for the Ollama client
        # The ollama library default timeout is None (unlimited), but httpx has internal limits
        # For embedding generation of large batches, we need explicit long timeouts
        #
        # The key is the 'read' timeout - this is how long httpx will wait for Ollama
        # to send response data. Embedding generation can take >90s for large batches.
        from httpx import Timeout
        from ollama import AsyncClient, Client

        # Configure explicit timeouts for all phases:
        # - connect: 30s (time to establish connection)
        # - read: 300s (time to read response - CRITICAL for long embedding operations)
        # - write: 30s (time to send request)
        # - pool: 30s (time to acquire connection from pool)
        timeout_config = Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

        # Create ollama clients directly with timeout parameter
        # The ollama.BaseClient accepts 'timeout' parameter directly
        async_client = AsyncClient(
            host=settings.ollama_embedding_url,
            timeout=timeout_config
        )

        sync_client = Client(
            host=settings.ollama_embedding_url,
            timeout=timeout_config
        )

        # Create OllamaEmbeddings but replace its clients with our configured ones
        self.embeddings = OllamaEmbeddings(
            base_url=settings.ollama_embedding_url,
            model=settings.ollama_embedding_model,
            keep_alive=settings.ollama_keep_alive
        )

        # Override the internal clients with our timeout-configured ones
        self.embeddings._async_client = async_client
        self.embeddings._client = sync_client

        logger.info(f"EmbeddingService initialized with URL: {settings.ollama_embedding_url}, Model: {settings.ollama_embedding_model}, Timeout: connect=30s, read=300s")

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