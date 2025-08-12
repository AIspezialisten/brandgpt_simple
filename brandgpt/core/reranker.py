from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self):
        if settings.reranker_enabled:
            self.model = CrossEncoder(settings.reranker_model)
        else:
            self.model = None
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        if not self.model or not settings.reranker_enabled:
            return documents[:top_k] if top_k else documents
        
        try:
            top_k = top_k or settings.reranker_top_k
            
            # Prepare pairs for reranking
            pairs = [[query, doc["text"]] for doc in documents]
            
            # Get reranking scores
            scores = self.model.predict(pairs)
            
            # Add rerank scores to documents
            for doc, score in zip(documents, scores):
                doc["rerank_score"] = float(score)
            
            # Sort by rerank score
            reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
            
            logger.info(f"Reranked {len(documents)} documents, returning top {top_k}")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}")
            # Return original documents if reranking fails
            return documents[:top_k] if top_k else documents