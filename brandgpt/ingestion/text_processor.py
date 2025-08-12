from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangchainDocument
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
    
    async def process(self, content: str, metadata: Dict[str, Any] = None) -> List[LangchainDocument]:
        try:
            # Create a document from the text content
            document = LangchainDocument(
                page_content=content,
                metadata=metadata or {}
            )
            
            # Split the document into chunks
            chunks = self.text_splitter.split_documents([document])
            
            logger.info(f"Processed text: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise