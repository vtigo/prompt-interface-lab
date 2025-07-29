"""
Simple OpenAI chat agent using LangChain.

This module provides a conservative, straightforward implementation of a chat agent
that integrates with OpenAI's API through LangChain. It prioritizes reliability
and error handling over complex features.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

# Configure logging
logger = logging.getLogger(__name__)


class ChatAgent:
    """
    A simple chat agent that handles conversations with OpenAI models.
    
    This class implements defensive programming practices:
    - Explicit error handling
    - Input validation
    - Clear configuration management
    - Proper logging
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize the chat agent with basic configuration.
        
        Args:
            model_name: The OpenAI model to use (defaults to gpt-3.5-turbo)
            temperature: Sampling temperature (0.0 to 1.0)
        
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If OpenAI API key is not available
        """
        # Validate inputs
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("Model name must be a non-empty string")
        
        if not isinstance(temperature, (int, float)) or not (0.0 <= temperature <= 1.0):
            raise ValueError("Temperature must be a number between 0.0 and 1.0")
        
        # Check for API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is required but not set"
            )
        
        self.model_name = model_name
        self.temperature = temperature
        
        try:
            # Initialize the OpenAI client through LangChain
            self.llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                openai_api_key=api_key
            )
            logger.info(f"ChatAgent initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")
            raise RuntimeError(f"Failed to initialize chat agent: {e}")
    
    def _convert_message_format(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert messages from the frontend format to LangChain format.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            List of LangChain message objects
            
        Raises:
            ValueError: If message format is invalid
        """
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        
        langchain_messages = []
        
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Each message must be a dictionary")
            
            if "role" not in message or "content" not in message:
                raise ValueError("Each message must have 'role' and 'content' keys")
            
            role = message["role"]
            content = message["content"]
            
            if not isinstance(content, str):
                raise ValueError("Message content must be a string")
            
            # Convert to appropriate LangChain message type
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))
            else:
                # Log unknown role but continue processing
                logger.warning(f"Unknown message role: {role}, treating as human message")
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Generate a response to the conversation.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If input is invalid
            RuntimeError: If generation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            # Convert messages to LangChain format
            langchain_messages = self._convert_message_format(messages)
            
            # Generate response
            logger.debug(f"Generating response for {len(messages)} messages")
            response = await self.llm.agenerate([langchain_messages])
            
            # Extract the response text
            if not response.generations or not response.generations[0]:
                raise RuntimeError("No response generated from the model")
            
            response_text = response.generations[0][0].text
            
            if not isinstance(response_text, str):
                raise RuntimeError("Invalid response format from model")
            
            logger.debug("Response generated successfully")
            return response_text
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")
    
    async def generate_streaming_response(self, messages: List[Dict[str, Any]]):
        """
        Generate a streaming response to the conversation.
        
        Args:
            messages: List of conversation messages
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            ValueError: If input is invalid
            RuntimeError: If generation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        try:
            # Convert messages to LangChain format
            langchain_messages = self._convert_message_format(messages)
            
            # Generate streaming response
            logger.debug(f"Generating streaming response for {len(messages)} messages")
            
            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise RuntimeError(f"Failed to generate streaming response: {e}")


def create_chat_agent(model_name: Optional[str] = None, temperature: Optional[float] = None) -> ChatAgent:
    """
    Factory function to create a ChatAgent with environment-based defaults.
    
    Args:
        model_name: Override default model name
        temperature: Override default temperature
        
    Returns:
        Configured ChatAgent instance
    """
    # Use environment variables for defaults, with fallbacks
    default_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    default_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Override with provided values
    final_model = model_name or default_model
    final_temperature = temperature if temperature is not None else default_temperature
    
    return ChatAgent(model_name=final_model, temperature=final_temperature)