"""Chat API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_qdrant
from app.core.exceptions import AuthenticationError
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationResponse,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageResponse,
)
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_chat_service(
    db: Session = Depends(get_db),
    qdrant = Depends(get_qdrant),
) -> ChatService:
    return ChatService(db, qdrant)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Send a chat message and get a response."""
    user = auth_service.get_current_user(token)
    
    response = await chat_service.send_message(
        user=user,
        message=request.message,
        report_id=request.report_id,
        conversation_id=request.conversation_id,
    )
    
    return ChatResponse(
        message_id=response["message_id"],
        conversation_id=response["conversation_id"],
        answer=response["answer"],
        citations=[
            CitationResponse(
                title=c["title"],
                url=c.get("url"),
                source_type=c["source_type"],
            )
            for c in response["citations"]
        ],
        is_emergency=response["is_emergency"],
        insufficient_evidence=response["insufficient_evidence"],
        created_at=response["created_at"],
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    page: int = 1,
    page_size: int = 20,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationListResponse:
    """List user's conversations."""
    user = auth_service.get_current_user(token)
    
    offset = (page - 1) * page_size
    conversations, total = chat_service.list_conversations(
        user=user,
        limit=page_size,
        offset=offset,
    )
    
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationDetailResponse:
    """Get a conversation with all messages."""
    user = auth_service.get_current_user(token)
    
    data = chat_service.get_conversation(user, conversation_id)
    
    return ConversationDetailResponse(
        conversation=ConversationResponse(**data["conversation"]),
        messages=[
            MessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                role=m["role"],
                content=m["content"],
                citations=[
                    CitationResponse(
                        title=c["title"],
                        url=c.get("url"),
                        source_type=c["source_type"],
                    )
                    for c in (m["citations"] or [])
                ] if m["citations"] else None,
                created_at=m["created_at"],
            )
            for m in data["messages"]
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: UUID,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a conversation."""
    user = auth_service.get_current_user(token)
    chat_service.delete_conversation(user, conversation_id)
