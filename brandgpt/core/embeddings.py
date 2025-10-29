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
        Generate embeddings for a list of texts with robust batch processing.

        Strategy for avoiding timeouts:
        - Use small batches (10 chunks) to ensure each request completes quickly
        - Each batch completes in ~15-30 seconds (well under proxy timeouts)
        - Progress logging for transparency
        - Graceful error handling per batch

        This approach is more robust than relying on long timeouts.
        """
        try:
            # ALWAYS use very small batches to stay under proxy timeouts
            # Even with proxy_read_timeout 30s, we need batches that complete quickly
            # Batch size of 5 ensures each request completes in ~10-20s (after cold start)
            # First batch with cold start: ~30-50s (model loading + 5 embeddings)
            batch_size = 5

            # Single text - no batching needed
            if len(texts) == 1:
                logger.info(f"Generating embedding for 1 document")
                embeddings = await asyncio.wait_for(
                    self.embeddings.aembed_documents(texts),
                    timeout=60.0  # 1 minute for single embedding
                )
                logger.info(f"✅ Generated embedding for 1 document")
                return embeddings

            # Multiple texts - use small batches
            logger.info(f"📦 Processing {len(texts)} documents in batches of {batch_size}")
            all_embeddings = []
            total_batches = (len(texts) + batch_size - 1) // batch_size

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_num = i//batch_size + 1

                logger.info(f"⚙️  Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")

                try:
                    # Very small batches for maximum reliability
                    # 5 chunks should complete in ~10-20 seconds (after cold start)
                    # First batch may take 30-50s with model loading
                    batch_embeddings = await asyncio.wait_for(
                        self.embeddings.aembed_documents(batch),
                        timeout=60.0  # 60 seconds per batch
                    )
                    all_embeddings.extend(batch_embeddings)
                    logger.info(f"✅ Batch {batch_num}/{total_batches} completed successfully")

                    # Small pause between batches to avoid overwhelming Ollama
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.3)

                except asyncio.TimeoutError:
                    logger.error(f"❌ Embedding batch {batch_num}/{total_batches} timed out after 60s")
                    raise TimeoutError(f"Embedding generation timed out for batch {batch_num}/{total_batches}")
                except Exception as batch_error:
                    logger.error(f"❌ Error in batch {batch_num}/{total_batches}: {str(batch_error)}")
                    raise

            logger.info(f"✅ Generated embeddings for all {len(texts)} documents")
            return all_embeddings

        except asyncio.TimeoutError:
            logger.error(f"❌ Embedding generation timed out for {len(texts)} documents")
            raise TimeoutError(f"Embedding generation timed out (60s per batch)")
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