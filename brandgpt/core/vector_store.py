from typing import List, Dict, Any, Optional
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document as LangchainDocument
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from brandgpt.config import settings
from brandgpt.core.embeddings import EmbeddingService
import uuid
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.embedding_service = EmbeddingService()
        self.collection_name = settings.qdrant_collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant_vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {str(e)}")
            raise
    
    async def add_documents(
        self,
        documents: List[LangchainDocument],
        session_id: str,
        user_id: int
    ) -> List[str]:
        try:
            texts = [doc.page_content for doc in documents]
            embeddings = await self.embedding_service.embed_documents(texts)
            
            points = []
            ids = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point_id = str(uuid.uuid4())
                ids.append(point_id)
                
                payload = {
                    "text": doc.page_content,
                    "session_id": session_id,
                    "user_id": user_id,
                    **doc.metadata
                }
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 20,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = await self.embedding_service.embed_query(query)
            
            filter_conditions = None
            if user_id:
                filter_conditions = {
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}}
                    ]
                }
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=filter_conditions,
                score_threshold=score_threshold
            )
            
            documents = []
            for result in results:
                documents.append({
                    "id": result.id,
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"}
                })
            
            logger.info(f"Found {len(documents)} documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    async def delete_by_session(self, session_id: str):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "session_id", "match": {"value": session_id}}
                        ]
                    }
                }
            )
            logger.info(f"Deleted documents for session: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise