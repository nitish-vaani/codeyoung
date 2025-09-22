# models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import datetime
from .db import Base
from .database_config import get_db_type

# Get database type to handle different column types
DB_TYPE = get_db_type()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True, nullable=True)  # Made nullable for default user
    password = Column(String(255), nullable=True)  # Made nullable for default user
    # user_uuid = Column(String)
    
    # Relationships with cascade options
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"
    
    model_id = Column(String(255), primary_key=True, index=True)
    model_name = Column(String(255), index=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    
    # Relationships with cascade options
    calls = relationship("Call", back_populates="model", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="model", cascade="all, delete-orphan")


class Call(Base):
    __tablename__ = "calls"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Call identifiers
    call_id = Column(String(255), index=True, nullable=True)
    
    # Foreign keys - made nullable with proper defaults
    model_id = Column(String(255), ForeignKey("models.model_id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=0)
    
    # Call-related fields
    name = Column(String(255), nullable=True)
    call_from = Column(String(50), nullable=True)
    call_to = Column(String(50), nullable=True)
    call_type = Column(String(50), nullable=True, default="Incoming")
    call_started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    call_duration = Column(Float, nullable=True)  # in seconds
    call_ended_at = Column(DateTime, nullable=True)
    call_status = Column(String(50), default="NA", nullable=True)
    
    # JSON fields with proper handling
    call_metadata = Column(JSON, nullable=True, default=dict)

    # Transfer related fields
    transfer_agent_name = Column(String(255), nullable=True)
    transfer_reason = Column(String(500), nullable=True)
    transfer_time = Column(DateTime, nullable=True)

    # Post call fields
    call_summary = Column(Text, nullable=True)
    call_transcription = Column(Text, nullable=True)
    call_recording_url = Column(String(500), nullable=True)
    call_conversation_quality = Column(JSON, nullable=True, default=dict)
    call_entity = Column(JSON, nullable=True, default=dict)

    # Relationships with proper back references
    model = relationship("Model", back_populates="calls")
    user = relationship("User", back_populates="calls")

    def __repr__(self):
        return f"<Call(id={self.id}, call_id='{self.call_id}', status='{self.call_status}')>"


class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key with proper constraint
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=0)
    
    # Feedback fields
    feedback_text = Column(Text, nullable=True)
    felt_neutral = Column(Integer, nullable=True)  # Fixed typo from "felt_neural"
    response_speed = Column(Integer, nullable=True)
    interruptions = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, created_at='{self.created_at}')>"


# Add these new models to your existing models.py file

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)  # Unique chat session ID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    room_id = Column(String(255), unique=True, index=True, nullable=False)  # LiveKit room ID
    participant_id = Column(String(255), index=True, nullable=False)  # userId_uuid_date format
    agent_id = Column(String(50), ForeignKey("models.model_id", ondelete="SET NULL"), nullable=False)
    agent_name = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    
    # Session status
    status = Column(String(50), default="active")  # active, ended, timeout
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Session metadata
    session_metadata = Column(JSON, nullable=True)  # Store additional session info
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    model = relationship("Model", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(255), unique=True, index=True, nullable=False)  # Unique message ID
    
    # Message content
    message_type = Column(String(50), nullable=False)  # user_message, agent_response, tool_start, tool_success, tool_error, system
    content = Column(Text, nullable=False)
    sender = Column(String(50), nullable=False)  # user, agent, system
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Message metadata
    message_metadata = Column(JSON, nullable=True)  # Store additional message info
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, message_id='{self.message_id}', sender='{self.sender}')>"




# Optional: Add indexes for better performance
from sqlalchemy import Index

# Create indexes for frequently queried columns
Index('idx_calls_call_id', Call.call_id)
Index('idx_calls_model_id', Call.model_id)
Index('idx_calls_user_id', Call.user_id)
Index('idx_calls_status', Call.call_status)
Index('idx_calls_started_at', Call.call_started_at)
Index('idx_feedback_user_id', Feedback.user_id)
Index('idx_feedback_created_at', Feedback.created_at)
Index('idx_chat_sessions_session_id', ChatSession.session_id)
Index('idx_chat_sessions_user_id', ChatSession.user_id)
Index('idx_chat_sessions_status', ChatSession.status)
Index('idx_chat_sessions_started_at', ChatSession.started_at)
Index('idx_chat_messages_session_id', ChatMessage.session_id)
Index('idx_chat_messages_message_id', ChatMessage.message_id)
Index('idx_chat_messages_timestamp', ChatMessage.timestamp)
