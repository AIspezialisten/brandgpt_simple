from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.ollama_llm_url,
            model=settings.ollama_llm_model,
            temperature=0.7,
            keep_alive=settings.ollama_keep_alive
        )
        logger.info(f"LLMService initialized with URL: {settings.ollama_llm_url}, Model: {settings.ollama_llm_model}")
    
    async def generate_response(
        self,
        query: str,
        context: List[str],
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        try:
            default_system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
            Use the context to provide accurate and relevant answers.
            If the answer cannot be found in the context, say so clearly."""

            system_prompt = system_prompt or default_system_prompt

            # Format context
            formatted_context = "\n\n".join(context)

            # Build messages list
            messages: List[BaseMessage] = [
                SystemMessagePromptTemplate.from_template(system_prompt).format()
            ]

            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Add current query with context
            current_query = f"Context:\n{formatted_context}\n\nQuestion: {query}\n\nAnswer:"
            messages.append(HumanMessage(content=current_query))

            # Generate response
            response = await self.llm.ainvoke(messages)

            logger.info("Generated LLM response with conversation history")
            return response.content

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise