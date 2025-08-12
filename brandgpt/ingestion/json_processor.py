from typing import List, Dict, Any
import json
from langchain.schema import Document as LangchainDocument
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class JSONProcessor:
    def __init__(self):
        pass
    
    async def process(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            # Parse JSON content
            json_data = json.loads(content) if isinstance(content, str) else content
            
            # Create a structured document for JSON storage
            document = {
                "data": json_data,
                "metadata": metadata or {},
                "type": "json"
            }
            
            logger.info(f"Processed JSON document")
            return document
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing JSON: {str(e)}")
            raise