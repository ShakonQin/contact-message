from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=True)

    avatars = relationship("Avatar", back_populates="owner", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="sender")


class Avatar(Base):
    """头像表 (存路径和情绪标签)"""
    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    emotion_tag = Column(String(20), nullable=False)

    owner = relationship("User", back_populates="avatars")


class Conversation(Base):
    """对话表 (支持 1对1 私聊)"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    is_group = Column(Boolean, default=False)
    agent_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation")


class ConversationParticipant(Base):
    """对话参与者表"""
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")


class Message(Base):
    """消息表 (存聊天记录)"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    detected_emotion = Column(String(20), default="neutral")
    timestamp = Column(DateTime, default=datetime.now, index=True)

    sender = relationship("User", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")