"""
Simple OpenAI chat agent using LangChain.

This module provides a conservative, straightforward implementation of a chat agent
that integrates with OpenAI's API through LangChain. It prioritizes reliability
and error handling over complex features.
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

# Configure logging
logger = logging.getLogger(__name__)


class ChatAgent:
    """
    A simple chat agent that handles conversations with OpenAI models.
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

        # Set up data directory path
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        if not self.data_dir.exists():
            logger.warning(f"Data directory does not exist: {self.data_dir}")

        try:
            self.llm = ChatOpenAI(model=model_name, temperature=temperature)
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

            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))
            else:
                logger.warning(
                    f"Unknown message role: {role}, treating as human message"
                )
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def read_file(self, filename: str) -> Dict[str, Any]:
        """
        Read a file from the data directory and return its contents.

        Args:
            filename: Name of the file to read

        Returns:
            Dictionary containing file information and content

        Raises:
            ValueError: If filename is invalid
            FileNotFoundError: If file doesn't exist
            RuntimeError: If file cannot be read
        """
        # Validate filename for security
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename cannot be empty")

        # Prevent path traversal attacks
        if ".." in filename or filename.startswith("/") or "\\" in filename:
            raise ValueError("Invalid filename: path traversal not allowed")

        filename = filename.strip()
        file_path = self.data_dir / filename

        # Ensure file is within data directory
        try:
            file_path = file_path.resolve()
            self.data_dir.resolve()
            if not str(file_path).startswith(str(self.data_dir.resolve())):
                raise ValueError("File access outside data directory not allowed")
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {filename}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            file_info = {
                "filename": filename,
                "content": content,
                "size": len(content.encode("utf-8")),
                "path": str(file_path.relative_to(self.data_dir)),
            }

            logger.debug(f"Read file: {filename} ({file_info['size']} bytes)")
            return file_info

        except UnicodeDecodeError:
            raise RuntimeError(f"File is not text-readable: {filename}")
        except Exception as e:
            logger.error(f"Failed to read file {filename}: {e}")
            raise RuntimeError(f"Failed to read file: {e}")

    def _detect_file_requests(self, message_content: str) -> List[str]:
        """
        Detect file reading requests in message content.

        Args:
            message_content: The message content to analyze

        Returns:
            List of filenames requested
        """
        import re

        # Patterns to detect file reading requests
        # Covers various ways users might request files
        patterns = [
            r"read\s+(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"show\s+(?:me\s+)?(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"get\s+(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"load\s+(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"open\s+(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"display\s+(?:the\s+)?(?:file\s+)?([^\s]+\.(?:txt|json|md|csv|log))",
            r"contents?\s+of\s+([^\s]+\.(?:txt|json|md|csv|log))",
            r"what\'?s\s+in\s+([^\s]+\.(?:txt|json|md|csv|log))",
            # More flexible pattern for filenames mentioned in context
            r"(?:file|document)\s+([^\s]+\.(?:txt|json|md|csv|log))",
            # Pattern for quoted filenames
            r'["\']([^"\']+\.(?:txt|json|md|csv|log))["\']',
        ]

        filenames = []
        for pattern in patterns:
            matches = re.findall(pattern, message_content, re.IGNORECASE)
            filenames.extend(matches)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(filenames))

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
            langchain_messages = self._convert_message_format(messages)

            logger.debug(f"Generating response for {len(messages)} messages")
            response = await self.llm.agenerate([langchain_messages])

            if not response.generations or not response.generations[0]:
                raise RuntimeError("No response generated from the model")

            response_text = response.generations[0][0].text

            if not isinstance(response_text, str):
                raise RuntimeError("Invalid response format from model")

            logger.debug("Response generated successfully")
            return response_text

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")

    async def generate_streaming_response(
        self, messages: List[Dict[str, Any]]
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """
        Generate a streaming response to the conversation, including file data when requested.

        Args:
            messages: List of conversation messages

        Yields:
            Text chunks or file data dictionaries

        Raises:
            ValueError: If input is invalid
            RuntimeError: If generation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        try:
            file_data_sent = []
            file_contents = {}
            if messages and messages[-1].get("role") == "user":
                last_message = messages[-1].get("content", "")
                requested_files = self._detect_file_requests(last_message)

                for filename in requested_files:
                    try:
                        file_info = self.read_file(filename)
                        file_data_sent.append(filename)
                        file_contents[filename] = file_info["content"]

                        yield {"type": "file_data", "data": file_info}
                        logger.info(f"File data sent for: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not read requested file {filename}: {e}")

            langchain_messages = self._convert_message_format(messages)

            if file_data_sent:
                context_parts = [
                    f"The user requested the following files. Here are their contents:",
                    f"IMPORTANT: Do NOT repeat or quote the file contents in your response. The file data is being sent separately to the UI.",
                    f"Only provide a brief acknowledgment that you've read the file(s) and answer any questions about them."
                ]
                for filename in file_data_sent:
                    content = file_contents[filename]
                    context_parts.append(
                        f"\n--- File: {filename} ---\n{content}\n--- End of {filename} ---"
                    )

                context_message = "\n".join(context_parts)
                langchain_messages.append(SystemMessage(content=context_message))

            logger.debug(f"Generating streaming response for {len(messages)} messages")

            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise RuntimeError(f"Failed to generate streaming response: {e}")


def create_chat_agent(
    model_name: Optional[str] = None, temperature: Optional[float] = None
) -> ChatAgent:
    """
    Factory function to create a ChatAgent with environment-based defaults.

    Args:
        model_name: Override default model name
        temperature: Override default temperature

    Returns:
        Configured ChatAgent instance
    """
    default_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    default_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    final_model = model_name or default_model
    final_temperature = temperature if temperature is not None else default_temperature

    return ChatAgent(model_name=final_model, temperature=final_temperature)
