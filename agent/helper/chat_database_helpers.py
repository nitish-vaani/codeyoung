"""
Database helpers specifically for chat sessions.
Handles chat session and message storage.
"""

from typing import Dict, Any
from datetime import datetime
from database.db_test.db import get_db_session
from database.db_test import models
from .logging_config import get_logger

logger = get_logger(__name__)

async def insert_chat_session_start(
    session_id: str, 
    user_id: int, 
    room_id: str, 
    participant_id: str,
    agent_id: str, 
    agent_name: str, 
    customer_name: str,
    session_metadata: Dict[str, Any] = None
) -> int:
    """Insert a new chat session start record"""
    try:
        db = get_db_session()
        
        # Create new chat session
        new_session = models.ChatSession(
            session_id=session_id,
            user_id=user_id,
            room_id=room_id,
            participant_id=participant_id,
            agent_id=agent_id,
            agent_name=agent_name,
            customer_name=customer_name,
            status="active",
            is_active=True,
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            session_metadata=session_metadata or {}
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"Created chat session: {session_id} for user {user_id}")
        return new_session.id
        
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

async def insert_chat_session_end(session_id: str, end_reason: str = "ended") -> bool:
    """Update chat session end record"""
    try:
        db = get_db_session()
        
        # Find and update the session
        session = db.query(models.ChatSession).filter(
            models.ChatSession.session_id == session_id
        ).first()
        
        if not session:
            logger.error(f"Chat session not found: {session_id}")
            return False
        
        session.ended_at = datetime.utcnow()
        session.status = end_reason
        session.is_active = False
        
        db.commit()
        logger.info(f"Ended chat session: {session_id} - {end_reason}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to end chat session: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

async def insert_chat_message(
    session_id: str,
    message_id: str,
    message_type: str,
    content: str,
    sender: str,
    message_metadata: Dict[str, Any] = None
) -> int:
    """Insert a chat message"""
    try:
        db = get_db_session()
        
        # Create new message
        new_message = models.ChatMessage(
            session_id=session_id,
            message_id=message_id,
            message_type=message_type,
            content=content,
            sender=sender,
            timestamp=datetime.utcnow(),
            message_metadata=message_metadata or {}
        )
        
        db.add(new_message)
        
        # Update session last activity
        session = db.query(models.ChatSession).filter(
            models.ChatSession.session_id == session_id
        ).first()
        
        if session:
            session.last_activity_at = datetime.utcnow()
        
        db.commit()
        db.refresh(new_message)
        
        logger.debug(f"Saved chat message: {message_id} in session {session_id}")
        return new_message.id
        
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

async def get_chat_session_by_id(session_id: str) -> Dict[str, Any]:
    """Get chat session information"""
    try:
        db = get_db_session()
        
        session = db.query(models.ChatSession).filter(
            models.ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return {}
        
        return {
            "id": session.id,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "room_id": session.room_id,
            "participant_id": session.participant_id,
            "agent_id": session.agent_id,
            "agent_name": session.agent_name,
            "customer_name": session.customer_name,
            "status": session.status,
            "is_active": session.is_active,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
            "session_metadata": session.session_metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        return {}
    finally:
        if db:
            db.close()

async def get_chat_messages(session_id: str, limit: int = 100) -> list:
    """Get messages for a chat session"""
    try:
        db = get_db_session()
        
        messages = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id
        ).order_by(models.ChatMessage.timestamp.asc()).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "message_id": msg.message_id,
                "message_type": msg.message_type,
                "content": msg.content,
                "sender": msg.sender,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "message_metadata": msg.message_metadata
            }
            for msg in messages
        ]
        
    except Exception as e:
        logger.error(f"Failed to get chat messages: {e}")
        return []
    finally:
        if db:
            db.close()

async def update_chat_session_activity(session_id: str) -> bool:
    """Update last activity time for a chat session"""
    try:
        db = get_db_session()
        
        session = db.query(models.ChatSession).filter(
            models.ChatSession.session_id == session_id
        ).first()
        
        if session:
            session.last_activity_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to update chat session activity: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()