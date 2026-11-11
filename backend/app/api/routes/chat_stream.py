"""Streaming chat endpoint."""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_qdrant
from app.core.exceptions import AuthenticationError
from app.services.auth_service import AuthService
from app.rag import RAGPipeline

router = APIRouter(prefix="/chat")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


@router.get("/stream")
async def stream_chat(
    message: str = Query(...),
    report_id: UUID | None = Query(default=None),
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
    qdrant = Depends(get_qdrant),
) -> StreamingResponse:
    """Stream a chat response using Server-Sent Events."""
    user = auth_service.get_current_user(token)
    pipeline = RAGPipeline(qdrant)
    
    async def generate():
        try:
            async for chunk in pipeline.answer_stream(
                query=message,
                user_id=user.id,
                report_id=report_id,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
