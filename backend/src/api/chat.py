"""
FastAPI chat endpoint with Vercel AI SDK streaming support.
"""

import json
import logging
from typing import AsyncGenerator, Optional
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

from ..model.chat_agent import create_chat_agent, ChatAgent
from .models import ChatRequest, StreamChunk, FinishData

logger = logging.getLogger(__name__)


class ChatEndpoint:
    """
    Handles chat API requests with streaming.
    """

    def __init__(self):
        self.agent: Optional[ChatAgent] = None

    def _get_agent(self) -> ChatAgent:
        """
        Get or create a chat agent instance.

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
                    status_code=500, detail="Failed to initialize chat service"
                )

        return self.agent

    async def _generate_stream_response(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response in Vercel AI SDK format.

        This method handles the streaming protocol required by the Vercel AI SDK.

        Args:
            request: Validated chat request

        Yields:
            Formatted stream chunks
        """
        try:
            agent = self._get_agent()

            messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "id": msg.id,
                }
                for msg in request.messages
            ]

            logger.debug(f"Processing chat request with {len(messages)} messages")

            response_chunks = []
            async for chunk in agent.generate_streaming_response(messages):
                # Handle file data objects
                if isinstance(chunk, dict) and chunk.get("type") == "file_data":
                    file_data = chunk.get("data", {})
                    # Send file data using the data stream protocol (type 2)
                    data_chunk = StreamChunk(type="data", content=json.dumps(file_data))
                    yield data_chunk.to_stream_format()
                # Handle text chunks
                elif chunk and isinstance(chunk, str):
                    response_chunks.append(chunk)
                    stream_chunk = StreamChunk(type="text", content=chunk)
                    yield stream_chunk.to_stream_format()

            finish_data = FinishData(
                finishReason="stop",
                usage={
                    "promptTokens": 0,  # TODO: Calculate actual usage
                    "completionTokens": len(response_chunks),
                },
            )

            finish_chunk = StreamChunk(
                type="finish", content=finish_data.to_json_string()
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
                content="An internal error occurred while generating the response",
            )
            yield error_chunk.to_stream_format()

    async def handle_chat_request(self, request: Request) -> StreamingResponse:
        """
        Handle incoming chat requests.

        Args:
            request: FastAPI request object

        Returns:
            StreamingResponse with proper headers

        Raises:
            HTTPException: For various error conditions
        """
        try:
            body = await request.json()
            chat_request = ChatRequest(**body)

            logger.info(
                f"Received chat request with {len(chat_request.messages)} messages"
            )

            response = StreamingResponse(
                self._generate_stream_response(chat_request),
                media_type="text/plain; charset=utf-8",
            )

            # Headers for Vercel AI SDK compatibility
            response.headers["x-vercel-ai-data-stream"] = "v1"
            response.headers["Cache-Control"] = "no-cache"

            return response

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request body: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")

        except ValueError as e:
            logger.warning(f"Request validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        except Exception as e:
            logger.error(f"Unexpected error handling chat request: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


chat_endpoint = ChatEndpoint()


async def chat_handler(request: Request) -> StreamingResponse:
    """
    FastAPI route handler for chat requests.

    Args:
        request: FastAPI request object

    Returns:
        StreamingResponse
    """
    return await chat_endpoint.handle_chat_request(request)
