"""
FastAPI chat endpoint with Vercel AI SDK streaming support.

This module implements a conservative, reliable chat API that follows the
Vercel AI SDK streaming protocol. It prioritizes error handling, type safety,
and clear separation of concerns.
"""

import json
import logging
from typing import AsyncGenerator
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

from ..model.chat_agent import create_chat_agent, ChatAgent
from .models import ChatRequest, ErrorResponse, StreamChunk, FinishData

# Configure logging
logger = logging.getLogger(__name__)


class ChatEndpoint:
    """
    Handles chat API requests with proper error handling and streaming.
    
    This class encapsulates all chat-related functionality following
    conservative design principles.
    """
    
    def __init__(self):
        """Initialize the chat endpoint."""
        self.agent: ChatAgent = None
    
    def _get_agent(self) -> ChatAgent:
        """
        Get or create a chat agent instance.
        
        This implements lazy initialization to avoid startup failures
        if OpenAI credentials are not available.
        
        Returns:
            ChatAgent instance
            
        Raises:
            HTTPException: If agent cannot be created
        """
        if self.agent is None:
            try:
                self.agent = create_chat_agent()
                logger.info("Chat agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize chat agent: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to initialize chat service"
                )
        
        return self.agent
    
    async def _generate_stream_response(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response in Vercel AI SDK format.
        
        This method handles the streaming protocol required by the Vercel AI SDK,
        including proper error handling and format compliance.
        
        Args:
            request: Validated chat request
            
        Yields:
            Formatted stream chunks
        """
        try:
            agent = self._get_agent()
            
            # Convert request messages to the format expected by the agent
            messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "id": msg.id
                }
                for msg in request.messages
            ]
            
            logger.debug(f"Processing chat request with {len(messages)} messages")
            
            # Stream the response
            full_response = ""
            async for chunk in agent.generate_streaming_response(messages):
                if chunk:  # Only yield non-empty chunks
                    full_response += chunk
                    
                    # Create text chunk in Vercel AI SDK format
                    stream_chunk = StreamChunk(type="text", content=chunk)
                    yield stream_chunk.to_stream_format()
            
            # Send completion data
            finish_data = FinishData(
                finishReason="stop",
                usage={
                    "promptTokens": 0,  # Would need to calculate actual usage
                    "completionTokens": len(full_response.split())
                }
            )
            
            finish_chunk = StreamChunk(
                type="finish", 
                content=finish_data.to_json_string()
            )
            yield finish_chunk.to_stream_format()
            
            logger.debug("Chat response streaming completed successfully")
            
        except ValueError as e:
            logger.warning(f"Invalid request data: {e}")
            error_chunk = StreamChunk(type="error", content=str(e))
            yield error_chunk.to_stream_format()
            
        except Exception as e:
            logger.error(f"Error during response generation: {e}")
            error_chunk = StreamChunk(
                type="error", 
                content="An internal error occurred while generating the response"
            )
            yield error_chunk.to_stream_format()
    
    async def handle_chat_request(self, request: Request) -> StreamingResponse:
        """
        Handle incoming chat requests.
        
        This is the main entry point for chat requests. It validates input,
        processes the request, and returns a streaming response.
        
        Args:
            request: FastAPI request object
            
        Returns:
            StreamingResponse with proper headers
            
        Raises:
            HTTPException: For various error conditions
        """
        try:
            # Parse and validate request body
            body = await request.json()
            chat_request = ChatRequest(**body)
            
            logger.info(f"Received chat request with {len(chat_request.messages)} messages")
            
            # Create streaming response with required headers
            response = StreamingResponse(
                self._generate_stream_response(chat_request),
                media_type="text/plain; charset=utf-8"
            )
            
            # Add required headers for Vercel AI SDK compatibility
            response.headers["x-vercel-ai-data-stream"] = "v1"
            response.headers["Cache-Control"] = "no-cache"
            
            return response
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request body: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in request body"
            )
            
        except ValueError as e:
            logger.warning(f"Request validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error handling chat request: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )


# Create a global instance for use in FastAPI routes
chat_endpoint = ChatEndpoint()


async def chat_handler(request: Request) -> StreamingResponse:
    """
    FastAPI route handler for chat requests.
    
    This is a simple wrapper around the ChatEndpoint class to maintain
    a clean separation between the routing logic and business logic.
    
    Args:
        request: FastAPI request object
        
    Returns:
        StreamingResponse
    """
    return await chat_endpoint.handle_chat_request(request)