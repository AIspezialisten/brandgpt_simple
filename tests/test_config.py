"""Test configuration and mocks for external dependencies."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any


# Mock Qdrant Client
class MockQdrantClient:
    def __init__(self, *args, **kwargs):
        self.collections = []
        self.points = []
    
    def get_collections(self):
        mock_collection = Mock()
        mock_collection.name = "brandgpt"
        return Mock(collections=[mock_collection])
    
    def create_collection(self, collection_name, vectors_config):
        return True
    
    def upsert(self, collection_name, points):
        self.points.extend(points)
        return True
    
    def search(self, collection_name, query_vector, limit=10, **kwargs):
        # Return mock search results
        results = []
        for i in range(min(3, limit)):  # Return up to 3 mock results
            mock_result = Mock()
            mock_result.id = f"doc_{i}"
            mock_result.score = 0.9 - (i * 0.1)
            mock_result.payload = {
                "text": f"Mock document {i} content related to the query",
                "source": f"test_doc_{i}.txt",
                "session_id": kwargs.get("query_filter", {}).get("must", [{}])[0].get("match", {}).get("value", "test_session")
            }
            results.append(mock_result)
        return results
    
    def delete(self, collection_name, points_selector):
        return True


# Mock Ollama Embeddings
class MockOllamaEmbeddings:
    def __init__(self, *args, **kwargs):
        pass
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        # Return mock embeddings (4096 dimensions as configured)
        return [[0.1] * 4096 for _ in texts]
    
    async def aembed_query(self, text: str) -> List[float]:
        return [0.1] * 4096


# Mock Chat Ollama
class MockChatOllama:
    def __init__(self, *args, **kwargs):
        pass
    
    async def ainvoke(self, messages):
        # Return a mock response based on the query
        query_text = ""
        for message in messages:
            if hasattr(message, 'content'):
                if "machine learning" in message.content.lower():
                    query_text = "machine learning"
                elif "nlp" in message.content.lower() or "natural language" in message.content.lower():
                    query_text = "natural language processing"
                break
        
        if query_text == "machine learning":
            response_text = """Machine learning is a method of data analysis that automates analytical model building. 
            It includes supervised learning, unsupervised learning, and reinforcement learning approaches."""
        elif query_text == "natural language processing":
            response_text = """Natural Language Processing (NLP) helps computers understand and interpret human language. 
            Key applications include text classification, sentiment analysis, and machine translation."""
        else:
            response_text = "I can help you with questions based on the provided context. Please ask about the topics in your documents."
        
        mock_response = Mock()
        mock_response.content = response_text
        return mock_response


# Mock Cross Encoder (Reranker)
class MockCrossEncoder:
    def __init__(self, *args, **kwargs):
        pass
    
    def predict(self, pairs):
        # Return mock relevance scores
        return [0.8 - (i * 0.1) for i in range(len(pairs))]


# Mock Unstructured Loader  
class MockUnstructuredLoader:
    def __init__(self, *args, **kwargs):
        self.file_path = args[0] if args else "test.pdf"
    
    def load(self):
        from langchain.schema import Document as LangchainDocument
        # Return mock documents from PDF
        return [
            LangchainDocument(
                page_content="This is a test document about artificial intelligence and machine learning. "
                           "Machine learning is a subset of AI that enables computers to learn from data.",
                metadata={"source": self.file_path, "page": 1}
            )
        ]


@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests."""
    with patch('brandgpt.core.vector_store.QdrantClient', MockQdrantClient), \
         patch('brandgpt.core.embeddings.OllamaEmbeddings', MockOllamaEmbeddings), \
         patch('brandgpt.retrieval.llm_service.ChatOllama', MockChatOllama), \
         patch('brandgpt.core.reranker.CrossEncoder', MockCrossEncoder), \
         patch('brandgpt.ingestion.pdf_processor.UnstructuredLoader', MockUnstructuredLoader):
        yield