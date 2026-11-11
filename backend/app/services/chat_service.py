"""Chat service for managing conversations and messages."""
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from qdrant_client import QdrantClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.models import Conversation, Message, Citation, User
from app.rag import RAGPipeline

logger = get_logger(__name__)


class ChatService:
    """Service for chat operations."""
    
    def __init__(self, db: Session, qdrant: QdrantClient):
        self.db = db
        self.rag = RAGPipeline(qdrant)
    
    async def send_message(
        self,
        user: User,
        message: str,
        report_id: UUID | None = None,
        conversation_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Send a message and get a response.
        
        Args:
            user: Current user
            message: User's message
            report_id: Optional report context
            conversation_id: Existing conversation or None for new
            
        Returns:
            Dict with response data
        """
        if conversation_id:
            conversation = self.db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id,
                )
            ).scalar_one_or_none()
            
            if not conversation:
                raise NotFoundError("Conversation", str(conversation_id))
        else:
            conversation = Conversation(
                user_id=user.id,
                report_id=report_id,
                title=message[:100] if len(message) > 100 else message,
            )
            self.db.add(conversation)
            self.db.flush()
        
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.db.add(user_message)
        self.db.flush()
        
        rag_response = await self.rag.answer(
            query=message,
            user_id=user.id,
            report_id=report_id or conversation.report_id,
        )
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=rag_response.answer,
        )
        self.db.add(assistant_message)
        self.db.flush()
        
        for citation_data in rag_response.citations:
            citation = Citation(
                message_id=assistant_message.id,
                source_url=citation_data["url"],
                source_title=citation_data["title"],
                source_type=citation_data["source_type"],
            )
            self.db.add(citation)
        
        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            "chat_message_sent",
            user_id=str(user.id),
            conversation_id=str(conversation.id),
            is_emergency=rag_response.is_emergency,
        )
        
        return {
            "message_id": assistant_message.id,
            "conversation_id": conversation.id,
            "answer": rag_response.answer,
            "citations": [
                {
                    "title": c["title"],
                    "url": c["url"],
                    "source_type": c["source_type"],
                }
                for c in rag_response.citations
            ],
            "is_emergency": rag_response.is_emergency,
            "insufficient_evidence": rag_response.insufficient_evidence,
            "created_at": assistant_message.created_at,
        }
    
    def get_conversation(
        self,
        user: User,
        conversation_id: UUID,
    ) -> dict[str, Any]:
        """Get a conversation with messages."""
        conversation = self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
        ).scalar_one_or_none()
        
        if not conversation:
            raise NotFoundError("Conversation", str(conversation_id))
        
        messages = self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        ).scalars().all()
        
        message_list = []
        for msg in messages:
            citations_query = self.db.execute(
                select(Citation).where(Citation.message_id == msg.id)
            ).scalars().all()
            
            citations = [
                {
                    "title": c.source_title,
                    "url": c.source_url,
                    "source_type": c.source_type,
                }
                for c in citations_query
            ] if citations_query else None
            
            message_list.append({
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "citations": citations,
                "created_at": msg.created_at,
            })
        
        return {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "report_id": conversation.report_id,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            },
            "messages": message_list,
        }
    
    def list_conversations(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """List user's conversations."""
        count_query = select(Conversation.id).where(
            Conversation.user_id == user.id
        )
        total = len(self.db.execute(count_query).scalars().all())
        
        query = (
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        conversations = list(self.db.execute(query).scalars().all())
        return conversations, total
    
    def delete_conversation(self, user: User, conversation_id: UUID) -> None:
        """Delete a conversation and all its messages."""
        conversation = self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
        ).scalar_one_or_none()
        
        if not conversation:
            raise NotFoundError("Conversation", str(conversation_id))
        
        messages = self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        ).scalars().all()
        
        for msg in messages:
            self.db.execute(
                Citation.__table__.delete().where(Citation.message_id == msg.id)
            )
            self.db.delete(msg)
        
        self.db.delete(conversation)
        self.db.commit()
        
        logger.info(
            "conversation_deleted",
            user_id=str(user.id),
            conversation_id=str(conversation_id),
        )
