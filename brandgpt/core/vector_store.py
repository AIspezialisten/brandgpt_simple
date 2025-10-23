from typing import List, Dict, Any, Optional
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document as LangchainDocument
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from brandgpt.config import settings
from brandgpt.core.embeddings import EmbeddingService
import uuid
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.client = None
        self.embedding_service = None
        self.collection_name = settings.qdrant_collection_name
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization to avoid startup issues."""
        if not self._initialized:
            try:
                self.client = QdrantClient(url=settings.qdrant_url)
                self.embedding_service = EmbeddingService()
                self._ensure_collection()
                self._initialized = True
                logger.info("VectorStore initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize VectorStore: {str(e)}")
                raise
    
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
        user_id: int,
        document_id: Optional[int] = None,
        group_id: Optional[str] = None
    ) -> List[str]:
        self._ensure_initialized()
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
                
                if document_id:
                    payload["document_id"] = document_id
                
                if group_id:
                    payload["group_id"] = group_id
                
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
        group_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search for documents with proper group_id and session_id logic.

        Logic:
        - Documents with group_id (without session_id) = Knowledge base for all sessions with that group_id
        - Documents with session_id = Additional knowledge sources only for that session

        When both group_id and session_id are provided:
          Find documents where (group_id = X AND session_id not set) OR (session_id = Y)
        """
        self._ensure_initialized()
        try:
            query_embedding = await self.embedding_service.embed_query(query)

            # Handle group_id and session_id logic with two searches if needed
            if group_id and session_id:
                # Perform two searches and combine results
                from qdrant_client.models import Filter, FieldCondition, MatchValue

                # Search 1: Documents with group_id (knowledge base - these should not have session_id)
                # We search for documents with the group_id and let the application filter
                # Note: In practice, documents with group_id should be ingested WITHOUT session_id
                filter_group_conditions = [
                    FieldCondition(key="group_id", match=MatchValue(value=group_id))
                ]
                if user_id:
                    filter_group_conditions.insert(0, FieldCondition(key="user_id", match=MatchValue(value=user_id)))

                filter_group = Filter(must=filter_group_conditions)

                results_group = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=filter_group,
                    score_threshold=score_threshold
                )

                # Filter out documents that have a session_id in the group results
                # (they should be session-specific, not knowledge base)
                filtered_group_results = [
                    r for r in results_group
                    if not r.payload.get("session_id") or r.payload.get("session_id") == ""
                ]

                # Search 2: Documents with session_id
                filter_session = Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ] if user_id else [
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ]
                )

                results_session = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=filter_session,
                    score_threshold=score_threshold
                )

                # Combine and deduplicate results
                seen_ids = set()
                combined_results = []
                for result in filtered_group_results + list(results_session):
                    if result.id not in seen_ids:
                        seen_ids.add(result.id)
                        combined_results.append(result)

                # Sort by score and limit
                combined_results.sort(key=lambda x: x.score, reverse=True)
                results = combined_results[:limit]

                logger.info(f"Combined search: {len(filtered_group_results)} from group (filtered from {len(results_group)}) + {len(results_session)} from session = {len(results)} total")

            elif group_id:
                # Only group_id: Find documents with this group_id (but NOT session-specific ones)
                # These are knowledge base documents that should not have a session_id
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                filter_conditions = Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="group_id", match=MatchValue(value=group_id))
                    ] if user_id else [
                        FieldCondition(key="group_id", match=MatchValue(value=group_id))
                    ]
                )

                results_raw = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=filter_conditions,
                    score_threshold=score_threshold
                )

                # Filter out documents that have a session_id (those are session-specific, not knowledge base)
                results = [
                    r for r in results_raw
                    if not r.payload.get("session_id") or r.payload.get("session_id") == ""
                ]

                logger.info(f"Group-only search: {len(results)} knowledge base docs (filtered from {len(results_raw)} total with group_id)")

            elif session_id:
                # Only session_id: Find documents with this session_id
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                filter_conditions = Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ] if user_id else [
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    ]
                )

                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=filter_conditions,
                    score_threshold=score_threshold
                )
            else:
                # No group_id or session_id: Search all user documents
                filter_conditions = None
                if user_id:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue
                    filter_conditions = Filter(
                        must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                    )

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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def delete_by_session(self, session_id: str):
        self._ensure_initialized()
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted documents for session: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def delete_by_document_id(self, document_id: int):
        self._ensure_initialized()
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted vectors for document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document vectors: {str(e)}")
            raise
    
    async def delete_by_group_id(self, group_id: str, user_id: int):
        self._ensure_initialized()
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="group_id",
                            match=MatchValue(value=group_id)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted vectors for group_id: {group_id} (user: {user_id})")
        except Exception as e:
            logger.error(f"Error deleting group vectors: {str(e)}")
            raise