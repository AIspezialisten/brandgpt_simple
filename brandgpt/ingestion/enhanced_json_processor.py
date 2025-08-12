from typing import List, Dict, Any, Union
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangchainDocument
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class EnhancedJSONProcessor:
    """
    Advanced JSON processor that creates better chunks for RAG by:
    1. Converting JSON to natural language descriptions
    2. Creating logical chunks based on JSON structure
    3. Preserving context and relationships
    4. Handling nested objects and arrays intelligently
    """
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _convert_value_to_text(self, value: Any, context_path: str = "") -> str:
        """Convert a JSON value to natural language text"""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "yes" if value else "no"
        elif isinstance(value, list):
            if not value:
                return "none"
            if len(value) == 1:
                return self._convert_value_to_text(value[0], context_path)
            elif all(isinstance(item, str) for item in value):
                return ", ".join(value)
            else:
                return "; ".join(self._convert_value_to_text(item, f"{context_path}[{i}]") 
                                for i, item in enumerate(value[:5]))  # Limit to first 5 items
        elif isinstance(value, dict):
            return self._dict_to_text(value, context_path)
        else:
            return str(value)
    
    def _dict_to_text(self, data: Dict[str, Any], context_path: str = "", level: int = 0) -> str:
        """Convert a dictionary to natural language text with proper formatting"""
        if not data:
            return ""
        
        text_parts = []
        indent = "  " * level
        
        for key, value in data.items():
            key_formatted = key.replace('_', ' ').title()
            value_path = f"{context_path}.{key}" if context_path else key
            
            if isinstance(value, dict):
                if value:  # Only process non-empty dicts
                    nested_text = self._dict_to_text(value, value_path, level + 1)
                    if nested_text:
                        text_parts.append(f"{indent}{key_formatted}: {nested_text}")
            elif isinstance(value, list):
                if value:  # Only process non-empty lists
                    list_text = self._process_list(value, key_formatted, value_path, level)
                    if list_text:
                        text_parts.append(list_text)
            else:
                formatted_value = self._convert_value_to_text(value, value_path)
                if formatted_value:
                    text_parts.append(f"{indent}{key_formatted}: {formatted_value}")
        
        return "\n".join(text_parts)
    
    def _process_list(self, items: List[Any], list_name: str, context_path: str, level: int = 0) -> str:
        """Process a list and convert it to readable text"""
        if not items:
            return ""
        
        indent = "  " * level
        text_parts = [f"{indent}{list_name}:"]
        
        # If all items are simple types (strings, numbers, booleans)
        if all(isinstance(item, (str, int, float, bool)) for item in items):
            if len(items) <= 5:
                for item in items:
                    text_parts.append(f"{indent}  - {self._convert_value_to_text(item, context_path)}")
            else:
                # Summarize long lists
                text_parts.append(f"{indent}  - {', '.join(str(item) for item in items[:3])}, and {len(items) - 3} more items")
        else:
            # Handle complex objects in the list
            for i, item in enumerate(items[:3]):  # Limit to first 3 items for readability
                if isinstance(item, dict):
                    item_text = self._dict_to_text(item, f"{context_path}[{i}]", level + 1)
                    if item_text:
                        text_parts.append(f"{indent}  Item {i+1}:")
                        text_parts.append(item_text)
                else:
                    text_parts.append(f"{indent}  - {self._convert_value_to_text(item, f'{context_path}[{i}]')}")
            
            if len(items) > 3:
                text_parts.append(f"{indent}  ... and {len(items) - 3} more items")
        
        return "\n".join(text_parts)
    
    def _create_structured_chunks(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """Create logical chunks based on JSON structure"""
        documents = []
        
        def process_object(obj: Dict[str, Any], path: str = "", parent_context: str = "") -> None:
            """Recursively process JSON objects and create meaningful chunks"""
            
            # Create a chunk for the current object if it has substantial content
            obj_text = self._dict_to_text(obj, path)
            if obj_text and len(obj_text.strip()) > 50:  # Only create chunk if substantial
                chunk_metadata = {
                    **metadata,
                    "json_path": path or "root",
                    "context": parent_context,
                    "chunk_type": "json_object"
                }
                
                # Add context header if we have parent context
                full_text = obj_text
                if parent_context:
                    full_text = f"Context: {parent_context}\n\n{obj_text}"
                
                documents.append(LangchainDocument(
                    page_content=full_text,
                    metadata=chunk_metadata
                ))
            
            # Process major sections as separate chunks
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                section_context = f"{parent_context} > {key.replace('_', ' ').title()}" if parent_context else key.replace('_', ' ').title()
                
                if isinstance(value, dict) and value:
                    # Create separate chunks for major objects
                    if len(json.dumps(value)) > 200:  # Only separate large objects
                        process_object(value, current_path, section_context)
                elif isinstance(value, list) and value:
                    # Process arrays with complex objects
                    if all(isinstance(item, dict) for item in value):
                        for i, item in enumerate(value[:5]):  # Process first 5 items
                            item_context = f"{section_context} > Item {i+1}"
                            if isinstance(item, dict):
                                process_object(item, f"{current_path}[{i}]", item_context)
        
        # Start processing from the root
        process_object(data, "", "Root")
        
        return documents
    
    async def process(self, content: str, metadata: Dict[str, Any] = None) -> List[LangchainDocument]:
        try:
            # Parse JSON content
            json_data = json.loads(content) if isinstance(content, str) else content
            
            # Enhanced metadata
            enhanced_metadata = {
                **(metadata or {}),
                "content_type": "json",
                "processor": "enhanced_json"
            }
            
            # Method 1: Create structured chunks based on JSON hierarchy
            structured_chunks = self._create_structured_chunks(json_data, enhanced_metadata)
            
            # Method 2: Create a comprehensive overview chunk
            overview_text = self._create_overview(json_data)
            if overview_text:
                overview_chunk = LangchainDocument(
                    page_content=f"Complete Overview:\n\n{overview_text}",
                    metadata={**enhanced_metadata, "chunk_type": "overview"}
                )
                structured_chunks.insert(0, overview_chunk)  # Add as first chunk
            
            # Method 3: Apply text splitting to ensure proper chunk sizes
            final_chunks = []
            for chunk in structured_chunks:
                if len(chunk.page_content) > settings.chunk_size * 2:
                    # Split large chunks
                    sub_chunks = self.text_splitter.split_documents([chunk])
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk)
            
            logger.info(f"Processed JSON: {len(final_chunks)} enhanced chunks created")
            return final_chunks
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            # Fallback: treat as regular text
            return self.text_splitter.split_text(content)
        except Exception as e:
            logger.error(f"Error processing JSON: {str(e)}")
            raise
    
    def _create_overview(self, data: Dict[str, Any]) -> str:
        """Create a comprehensive overview of the JSON data"""
        try:
            overview_parts = []
            
            # Extract key information for overview
            if isinstance(data, dict):
                # Look for common patterns and create summaries
                for key, value in data.items():
                    key_formatted = key.replace('_', ' ').title()
                    
                    if isinstance(value, dict):
                        # Summarize object
                        obj_keys = list(value.keys())[:5]
                        summary = f"{key_formatted} contains information about: {', '.join(k.replace('_', ' ') for k in obj_keys)}"
                        if len(value) > 5:
                            summary += f" (and {len(value) - 5} more fields)"
                        overview_parts.append(summary)
                    
                    elif isinstance(value, list):
                        # Summarize array
                        if value:
                            item_type = "items"
                            if isinstance(value[0], dict):
                                # If first item is object, describe its structure
                                first_keys = list(value[0].keys())[:3]
                                item_type = f"entries with {', '.join(k.replace('_', ' ') for k in first_keys)}"
                            overview_parts.append(f"{key_formatted} contains {len(value)} {item_type}")
                    
                    elif isinstance(value, (str, int, float)):
                        # Include direct values for key fields
                        if key.lower() in ['name', 'title', 'description', 'summary']:
                            overview_parts.append(f"{key_formatted}: {value}")
            
            return ". ".join(overview_parts) + "." if overview_parts else ""
            
        except Exception as e:
            logger.warning(f"Error creating overview: {str(e)}")
            return ""