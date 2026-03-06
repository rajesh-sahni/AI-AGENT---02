"""
Pydantic models for AI Agent chat requests and responses.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to send a chat message to the AI agent."""

    message: str = Field(..., description="User message to send")
    model: str = Field(
        default="deepseek-r1:1.5b",
        description="Ollama model name (e.g. deepseek-r1:1.5b)",
    )
    history: list[ChatMessage] = Field(default_factory=list, description="Previous chat history")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response from the AI agent."""

    message: str = Field(..., description="Assistant's reply")
    model: str = Field(..., description="Model used")
    done: bool = Field(default=True, description="Whether the response is complete")
