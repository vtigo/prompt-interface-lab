"""
Request and response models for the chat API.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
import uuid
import json


class ChatMessage(BaseModel):
    """
    Represents a single message in a conversation.
    """

    id: Optional[str] = Field(None, description="Unique identifier for the message")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="The role of the message sender"
    )
    content: str = Field(..., description="The actual message content")

    @field_validator("content")
    def content_must_not_be_empty(cls, v):
        """Ensure message content is not empty or only whitespace."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

    @field_validator("id", mode="before")
    def generate_id_if_missing(cls, v):
        """Generate a UUID if message ID is not provided."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return str(uuid.uuid4())
        if isinstance(v, str):
            return v.strip()
        return str(v)


class ChatRequest(BaseModel):
    """
    Request model for the chat endpoint.
    """

    messages: List[ChatMessage] = Field(
        ..., description="List of messages in the conversation"
    )
    id: Optional[str] = Field(None, description="Optional conversation ID")

    # Additional fields that might be sent by the frontend
    userId: Optional[str] = Field(None, description="Optional user identifier")
    sessionId: Optional[str] = Field(None, description="Optional session identifier")

    @field_validator("messages")
    def messages_must_not_be_empty(cls, v):
        """Ensure at least one message is provided."""
        if not v:
            raise ValueError("At least one message is required")
        return v

    @field_validator("messages")
    def last_message_must_be_user(cls, v):
        """
        Ensure the last message is from a user.
        """
        if v and v[-1].role != "user":
            raise ValueError("Last message must be from user")
        return v


class ChatResponse(BaseModel):
    """
    Response model for non-streaming chat responses.
    """

    message: str = Field(..., description="The generated response")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """

    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

    @classmethod
    def from_exception(cls, error: Exception, error_type: str = "internal_error"):
        """
        Create an ErrorResponse from an exception.

        Args:
            error: The exception that occurred
            error_type: Classification of the error

        Returns:
            ErrorResponse instance
        """
        return cls(
            error=str(error),
            error_type=error_type,
            details={"exception_type": type(error).__name__},
        )


class StreamChunk(BaseModel):
    """
    Model for individual chunks in a streaming response.

    This represents the structure of data sent in streaming responses,
    following the Vercel AI SDK format.
    """

    type: Literal["text", "data", "error", "finish"] = Field(
        ..., description="Type of stream chunk"
    )
    content: str = Field(..., description="Chunk content")

    def to_stream_format(self) -> str:
        """
        Convert the chunk to the Vercel AI SDK stream format.

        Returns:
            Formatted string ready for streaming
        """
        if self.type == "text":
            return f"0:{json.dumps(self.content)}\n"
        elif self.type == "data":
            return f"2:[{self.content}]\n"
        elif self.type == "error":
            return f"3:{json.dumps(self.content)}\n"
        elif self.type == "finish":
            return f"d:{self.content}\n"
        else:
            return f"0:{json.dumps(self.content)}\n"


class FinishData(BaseModel):
    """
    Model for the finish data sent at the end of a stream.
    """

    finishReason: Literal["stop", "length", "error"] = Field(
        default="stop", description="Reason the generation finished"
    )
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage information")

    def to_json_string(self) -> str:
        """
        Convert to JSON string for streaming.

        Returns:
            JSON string representation
        """
        return self.model_dump_json()
