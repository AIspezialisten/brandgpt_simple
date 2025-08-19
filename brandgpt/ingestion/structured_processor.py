"""
Structured data processor for maintaining original data structure while enabling RAG.
Supports backward compatibility with v1 API structured data ingestion.
"""

from typing import List, Dict, Any
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangchainDocument
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class StructuredDataProcessor:
    """
    Process structured data (JSON objects/arrays) while preserving original structure.
    Creates searchable content while maintaining data integrity for retrieval.
    """
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", ",", " ", ""]
        )
    
    def process(self, data: Dict[str, Any], metadata: Dict[str, Any] = None) -> List[LangchainDocument]:
        """
        Process structured data maintaining original structure.
        
        Args:
            data: Dictionary or list of dictionaries containing structured data
            metadata: Additional metadata to attach to documents
        
        Returns:
            List of LangchainDocument objects with preserved structure
        """
        documents = []
        base_metadata = metadata or {}
        
        try:
            # Handle both single objects and arrays
            items = data if isinstance(data, list) else [data]
            
            for idx, item in enumerate(items):
                # Generate searchable text representation
                search_text = self._generate_search_text(item)
                
                # Create document with original structure preserved
                doc_metadata = {
                    **base_metadata,
                    "content_type": "structured",
                    "original_structure": json.dumps(item),  # Preserve exact structure
                    "index": idx,
                    "data_type": type(item).__name__
                }
                
                # Add object ID if present (for backward compatibility)
                if isinstance(item, dict):
                    if "id" in item:
                        doc_metadata["object_id"] = item["id"]
                    if "type" in item:
                        doc_metadata["object_type"] = item["type"]
                    if "name" in item:
                        doc_metadata["object_name"] = item["name"]
                
                # Create chunks for searchability
                if len(search_text) > settings.chunk_size:
                    chunks = self.text_splitter.split_text(search_text)
                    for chunk_idx, chunk in enumerate(chunks):
                        chunk_metadata = {
                            **doc_metadata,
                            "chunk_index": chunk_idx,
                            "total_chunks": len(chunks)
                        }
                        documents.append(
                            LangchainDocument(
                                page_content=chunk,
                                metadata=chunk_metadata
                            )
                        )
                else:
                    documents.append(
                        LangchainDocument(
                            page_content=search_text,
                            metadata=doc_metadata
                        )
                    )
            
            logger.info(f"Processed {len(items)} structured items into {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing structured data: {str(e)}")
            return []
    
    def _generate_search_text(self, item: Any, indent: int = 0) -> str:
        """
        Generate human-readable, searchable text from structured data.
        Maintains hierarchy and relationships for better RAG performance.
        """
        if item is None:
            return "null"
        
        if isinstance(item, (str, int, float, bool)):
            return str(item)
        
        if isinstance(item, list):
            texts = []
            for i, element in enumerate(item):
                element_text = self._generate_search_text(element, indent)
                texts.append(f"Item {i + 1}: {element_text}")
            return "\n".join(texts)
        
        if isinstance(item, dict):
            lines = []
            for key, value in item.items():
                # Create readable key names
                readable_key = key.replace("_", " ").replace("-", " ").title()
                
                if isinstance(value, (dict, list)):
                    lines.append(f"{readable_key}:")
                    value_text = self._generate_search_text(value, indent + 2)
                    lines.append(f"  {value_text}")
                else:
                    value_text = self._generate_search_text(value, indent)
                    lines.append(f"{readable_key}: {value_text}")
            
            return "\n".join(lines)
        
        return str(item)
    
    def retrieve_original(self, metadata: Dict[str, Any]) -> Any:
        """
        Retrieve the original structured data from document metadata.
        
        Args:
            metadata: Document metadata containing original_structure
        
        Returns:
            Original structured data object
        """
        if "original_structure" in metadata:
            try:
                return json.loads(metadata["original_structure"])
            except json.JSONDecodeError:
                logger.error("Failed to decode original structure from metadata")
                return None
        return None