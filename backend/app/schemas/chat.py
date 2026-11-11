"""Chat Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request for chat message."""
    message: str
    report_id: UUID | None = None
    conversation_id: UUID | None = None


class CitationResponse(BaseModel):
    """Citation in a chat response."""
    title: str
    url: str | None = None
    source_type: str


class ChatResponse(BaseModel):
    """Response for chat message."""
    message_id: UUID
    conversation_id: UUID
    answer: str
    citations: list[CitationResponse]
    is_emergency: bool = False
    insufficient_evidence: bool = False
    created_at: datetime


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: UUID
    title: str | None = None
    report_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Response for a message."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    citations: list[CitationResponse] | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """Response for conversation with messages."""
    conversation: ConversationResponse
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    """Response for list of conversations."""
    items: list[ConversationResponse]
    total: int
