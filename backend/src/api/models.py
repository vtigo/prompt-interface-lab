"""
Request and response models for the chat API.

This module defines Pydantic models that provide type safety and validation
for API requests and responses. Following conservative coding principles,
these models are simple, explicit, and well-documented.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator


class ChatMessage(BaseModel):
    """
    Represents a single message in a conversation.
    
    This model validates the structure of messages sent from the frontend
    and ensures they contain all required fields with proper types.
    """
    id: str = Field(..., description="Unique identifier for the message")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="The role of the message sender"
    )
    content: str = Field(..., description="The actual message content")
    
    @validator("content")
    def content_must_not_be_empty(cls, v):
        """Ensure message content is not empty or only whitespace."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()
    
    @validator("id")
    def id_must_not_be_empty(cls, v):
        """Ensure message ID is not empty."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Message ID cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """
    Request model for the chat endpoint.
    
    This model validates incoming chat requests and ensures they contain
    all necessary information for processing.
    """
    messages: List[ChatMessage] = Field(
        ..., description="List of messages in the conversation"
    )
    id: Optional[str] = Field(
        None, description="Optional conversation ID"
    )
    
    # Additional fields that might be sent by the frontend
    userId: Optional[str] = Field(None, description="Optional user identifier")
    sessionId: Optional[str] = Field(None, description="Optional session identifier")
    
    @validator("messages")
    def messages_must_not_be_empty(cls, v):
        """Ensure at least one message is provided."""
        if not v:
            raise ValueError("At least one message is required")
        return v
    
    @validator("messages")
    def last_message_must_be_user(cls, v):
        """
        Ensure the last message is from a user.
        
        This is a defensive check to ensure we're responding to user input.
        """
        if v and v[-1].role != "user":
            raise ValueError("Last message must be from user")
        return v


class ChatResponse(BaseModel):
    """
    Response model for non-streaming chat responses.
    
    This model is provided for completeness but typically won't be used
    since we'll be streaming responses.
    """
    message: str = Field(..., description="The generated response")
    conversation_id: Optional[str] = Field(
        None, description="Conversation identifier"
    )
    tokens_used: Optional[int] = Field(
        None, description="Number of tokens consumed"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    
    This provides a consistent error format across all endpoints.
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
            details={"exception_type": type(error).__name__}
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
            return f'0:"{self.content}"\n'
        elif self.type == "data":
            return f'2:[{self.content}]\n'
        elif self.type == "error":
            return f'3:"{self.content}"\n'
        elif self.type == "finish":
            return f'd:{self.content}\n'
        else:
            # Fallback - should not happen with Literal type
            return f'0:"{self.content}"\n'


class FinishData(BaseModel):
    """
    Model for the finish data sent at the end of a stream.
    
    This follows the Vercel AI SDK format for completion metadata.
    """
    finishReason: Literal["stop", "length", "error"] = Field(
        default="stop", description="Reason the generation finished"
    )
    usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage information"
    )
    
    def to_json_string(self) -> str:
        """
        Convert to JSON string for streaming.
        
        Returns:
            JSON string representation
        """
        return self.model_dump_json()