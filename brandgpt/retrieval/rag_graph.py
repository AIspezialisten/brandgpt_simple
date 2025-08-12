from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from brandgpt.core import VectorStore, Reranker
from brandgpt.retrieval.llm_service import LLMService
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
    query: str
    user_id: Optional[int]
    system_prompt: Optional[str]
    retrieved_docs: List[Dict[str, Any]]
    reranked_docs: List[Dict[str, Any]]
    context: List[str]
    response: str
    error: Optional[str]


class RAGGraph:
    def __init__(self):
        self.vector_store = VectorStore()
        self.reranker = Reranker()
        self.llm_service = LLMService()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("retrieve", self.retrieve_documents)
        workflow.add_node("rerank", self.rerank_documents)
        workflow.add_node("prepare_context", self.prepare_context)
        workflow.add_node("generate", self.generate_response)
        
        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "prepare_context")
        workflow.add_edge("prepare_context", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    async def retrieve_documents(self, state: RAGState) -> RAGState:
        try:
            documents = await self.vector_store.search(
                query=state["query"],
                user_id=state.get("user_id"),
                limit=settings.reranker_candidates
            )
            state["retrieved_docs"] = documents
            logger.info(f"Retrieved {len(documents)} documents")
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            state["error"] = str(e)
            state["retrieved_docs"] = []
        
        return state
    
    async def rerank_documents(self, state: RAGState) -> RAGState:
        try:
            if not state["retrieved_docs"]:
                state["reranked_docs"] = []
                return state
            
            reranked = await self.reranker.rerank(
                query=state["query"],
                documents=state["retrieved_docs"],
                top_k=settings.reranker_top_k
            )
            state["reranked_docs"] = reranked
            logger.info(f"Reranked to {len(reranked)} documents")
        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}")
            # Fallback to original documents
            state["reranked_docs"] = state["retrieved_docs"][:settings.reranker_top_k]
        
        return state
    
    async def prepare_context(self, state: RAGState) -> RAGState:
        try:
            # Extract text from reranked documents
            context = []
            for doc in state["reranked_docs"]:
                text = doc.get("text", "")
                if text:
                    # Add source information if available
                    source = doc.get("metadata", {}).get("source", "")
                    if source:
                        context.append(f"[Source: {source}]\n{text}")
                    else:
                        context.append(text)
            
            state["context"] = context
            logger.info(f"Prepared context with {len(context)} segments")
        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}")
            state["context"] = []
        
        return state
    
    async def generate_response(self, state: RAGState) -> RAGState:
        try:
            if not state["context"]:
                state["response"] = "I couldn't find any relevant information to answer your question."
                return state
            
            response = await self.llm_service.generate_response(
                query=state["query"],
                context=state["context"],
                system_prompt=state.get("system_prompt")
            )
            state["response"] = response
            logger.info("Generated response")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            state["response"] = f"An error occurred while generating the response: {str(e)}"
            state["error"] = str(e)
        
        return state
    
    async def process_query(
        self,
        query: str,
        user_id: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        initial_state: RAGState = {
            "query": query,
            "user_id": user_id,
            "system_prompt": system_prompt,
            "retrieved_docs": [],
            "reranked_docs": [],
            "context": [],
            "response": "",
            "error": None
        }
        
        try:
            result = await self.graph.ainvoke(initial_state)
            return {
                "response": result["response"],
                "sources": [
                    {
                        "text": doc.get("text", "")[:200] + "...",
                        "metadata": doc.get("metadata", {})
                    }
                    for doc in result["reranked_docs"][:3]
                ],
                "error": result.get("error")
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": f"An error occurred: {str(e)}",
                "sources": [],
                "error": str(e)
            }