# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models
from typing import List, Dict, Optional



# 用户相关 (Users)
def get_user_by_nickname(db: Session, nickname: str):
    return db.query(models.User).filter(models.User.nickname == nickname).first()


def create_user(db: Session, nickname: str, password: str, ip_address: str):
    # 简单的创建逻辑
    db_user = models.User(nickname=nickname, password=password, ip_address=ip_address)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



# 头像相关 (Avatars)

def create_avatar(db: Session, user_id: int, image_path: str, emotion_tag: str):
    db_avatar = models.Avatar(user_id=user_id, image_path=image_path, emotion_tag=emotion_tag)
    db.add(db_avatar)
    db.commit()
    db.refresh(db_avatar)
    return db_avatar



def get_avatar_url(db: Session, user_id: int, emotion: str) -> str:
    """
    根据用户ID和情绪标签查找头像。
    """
    #尝试精确匹配
    avatar = db.query(models.Avatar).filter(
        models.Avatar.user_id == user_id,
        models.Avatar.emotion_tag == emotion
    ).first()

    if avatar:
        return avatar.image_path

    # 降级到 'neutral'
    neutral_avatar = db.query(models.Avatar).filter(
        models.Avatar.user_id == user_id,
        models.Avatar.emotion_tag == "neutral"
    ).first()

    if neutral_avatar:
        return neutral_avatar.image_path

    # 最后的保底
    return "/static/default_avatar.png"






# 消息相关 (Messages)
def create_message(db: Session, user_id: int, content: str, emotion: str):
    """保存消息，同时记录当时 AI 分析出的情绪"""
    db_message = models.Message(
        user_id=user_id,
        content=content,
        detected_emotion=emotion
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_recent_messages_for_agent(db: Session, limit: int = 10) -> List[Dict]:
    """
    获取最近 N 条消息，并格式化为 Agent 可读的格式。
    注意：数据库查询出来是按时间倒序(最新的在最前)，我们需要反转为正序(按时间发生顺序)给 AI。
    """
    # 联合查询：我们需要 User 表里的 nickname
    messages = db.query(models.Message, models.User.nickname) \
        .join(models.User, models.Message.user_id == models.User.id) \
        .order_by(models.Message.timestamp.desc()) \
        .limit(limit) \
        .all()


    history = []
    # 反转列表，让最旧的消息在前面
    for msg, nickname in reversed(messages):
        history.append({
            "nickname": nickname,
            "content": msg.content
        })

    return history