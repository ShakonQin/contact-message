from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=True)  # 记录局域网 IP

    # 关系
    avatars = relationship("Avatar", back_populates="owner", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="sender")


class Avatar(Base):
    """头像表 (存路径和情绪标签)"""
    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(255), nullable=False)  # 例如: /static/avatars/u1_happy.png
    emotion_tag = Column(String(20), nullable=False)  # 例如: happy, sad, angry

    # 关系
    owner = relationship("User", back_populates="avatars")


class Message(Base):
    """消息表 (存聊天记录)"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)

    # 存储 AI 当时判断出的情绪
    detected_emotion = Column(String(20), default="neutral")

    # 加上 index=True，
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # 关系
    sender = relationship("User", back_populates="messages")