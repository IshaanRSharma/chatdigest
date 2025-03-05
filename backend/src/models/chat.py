from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

class ChatMessage(BaseModel):
    """
    Represents a single message in a chat conversation
    """
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

class ParsedChat(BaseModel):
    """
    Represents a parsed chat log with structured messages
    """
    messages: List[ChatMessage] = Field(..., description="List of parsed chat messages")
    format_detected: str = Field(..., description="Format detected in the chat log")
    token_count: int = Field(..., description="Estimated token count")
    message_count: int = Field(..., description="Number of messages")
    raw_content: str = Field(..., description="Original raw content")

class SummaryRequest(BaseModel):
    """
    Request model for summarizing a chat log
    """
    chat_content: str = Field(..., description="Raw chat content to summarize")
    target_llm: str = Field(..., description="Target LLM to optimize for")
    max_tokens: Optional[int] = Field(None, description="Custom max token limit (overrides default for LLM)")
    preserve_code: bool = Field(True, description="Whether to preserve code blocks")
    include_system_prompts: bool = Field(True, description="Whether to include system prompts")

class SummaryResponse(BaseModel):
    """
    Response model for summarized chat
    """
    summary: str = Field(..., description="Summarized chat content")
    original_tokens: int = Field(..., description="Original token count")
    summary_tokens: int = Field(..., description="Summarized token count")
    reduction: float = Field(..., description="Percentage reduction in tokens")
    format: str = Field(..., description="Format used for the summary")

class LLMType(BaseModel):
    """
    Model representing an LLM type with its properties
    """
    id: str = Field(..., description="Identifier for the LLM")
    name: str = Field(..., description="Display name for the LLM")
    token_limit: int = Field(..., description="Token limit for the LLM")
    format: Optional[str] = Field(None, description="Format identifier")
    recommended: Optional[bool] = Field(False, description="Whether this LLM is recommended")