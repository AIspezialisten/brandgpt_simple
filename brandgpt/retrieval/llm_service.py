from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseMessage
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_llm_model,
            temperature=0.7
        )
    
    async def generate_response(
        self,
        query: str,
        context: List[str],
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            default_system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
            Use the context to provide accurate and relevant answers.
            If the answer cannot be found in the context, say so clearly."""
            
            system_prompt = system_prompt or default_system_prompt
            
            # Format context
            formatted_context = "\n\n".join(context)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(
                    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
                )
            ])
            
            # Generate response
            messages = prompt.format_messages(
                context=formatted_context,
                question=query
            )
            
            response = await self.llm.ainvoke(messages)
            
            logger.info("Generated LLM response")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise