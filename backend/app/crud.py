import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from . import models
from typing import List, Dict, Optional


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# 用户相关 (Users)
def get_user_by_nickname(db: Session, nickname: str):
    return db.query(models.User).filter(models.User.nickname == nickname).first()


def create_user(db: Session, nickname: str, password: str, ip_address: str):
    db_user = models.User(nickname=nickname, password=hash_password(password), ip_address=ip_address)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_users(db: Session):
    return db.query(models.User).all()


# 头像相关 (Avatars)
def create_avatar(db: Session, user_id: int, image_path: str, emotion_tag: str):
    db_avatar = models.Avatar(user_id=user_id, image_path=image_path, emotion_tag=emotion_tag)
    db.add(db_avatar)
    db.commit()
    db.refresh(db_avatar)
    return db_avatar


def get_avatar_url(db: Session, user_id: int, emotion: str) -> str:
    avatar = db.query(models.Avatar).filter(
        models.Avatar.user_id == user_id,
        models.Avatar.emotion_tag == emotion
    ).first()
    if avatar:
        return avatar.image_path

    neutral_avatar = db.query(models.Avatar).filter(
        models.Avatar.user_id == user_id,
        models.Avatar.emotion_tag == "neutral"
    ).first()
    if neutral_avatar:
        return neutral_avatar.image_path

    return "/static/default_avatar.svg"


# 对话相关 (Conversations)
def get_or_create_dm_conversation(db: Session, user1_id: int, user2_id: int) -> models.Conversation:
    """查找两个用户之间的私聊对话，不存在则创建"""
    # 查找已有对话：两个参与者且不是群聊
    existing = db.query(models.Conversation).join(models.ConversationParticipant).filter(
        models.Conversation.is_group == False,
        models.ConversationParticipant.user_id.in_([user1_id, user2_id])
    ).group_by(models.Conversation.id).having(
        func.count(models.ConversationParticipant.id) == 2
    ).all()

    for conv in existing:
        participant_ids = {p.user_id for p in conv.participants}
        if participant_ids == {user1_id, user2_id}:
            return conv

    # 创建新对话
    conv = models.Conversation(is_group=False, agent_active=False)
    db.add(conv)
    db.flush()
    p1 = models.ConversationParticipant(conversation_id=conv.id, user_id=user1_id)
    p2 = models.ConversationParticipant(conversation_id=conv.id, user_id=user2_id)
    db.add_all([p1, p2])
    db.commit()
    db.refresh(conv)
    return conv


def get_user_conversations(db: Session, user_id: int) -> List[Dict]:
    """获取用户的所有对话，带最后一条消息预览"""
    participations = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.user_id == user_id
    ).all()

    result = []
    for p in participations:
        conv = p.conversation
        # 获取对方用户信息
        other_participants = [pp for pp in conv.participants if pp.user_id != user_id]
        other_user = other_participants[0].user if other_participants else None

        # 获取最后一条消息
        last_msg = db.query(models.Message).filter(
            models.Message.conversation_id == conv.id
        ).order_by(models.Message.timestamp.desc()).first()

        result.append({
            "conversation_id": conv.id,
            "agent_active": conv.agent_active,
            "other_user": {
                "id": other_user.id,
                "nickname": other_user.nickname,
            } if other_user else None,
            "last_message": {
                "content": last_msg.content[:50] if last_msg else "",
                "timestamp": last_msg.timestamp.isoformat() if last_msg else None,
                "sender_nickname": last_msg.sender.nickname if last_msg else "",
            } if last_msg else None,
        })

    # 按最后消息时间排序
    result.sort(key=lambda x: x["last_message"]["timestamp"] if x["last_message"] else "", reverse=True)
    return result


def get_conversation_messages(db: Session, conversation_id: int, limit: int = 50) -> List[Dict]:
    """获取对话中的消息，带头像"""
    messages = db.query(models.Message, models.User.nickname).join(
        models.User, models.Message.user_id == models.User.id
    ).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.timestamp.desc()).limit(limit).all()

    result = []
    for msg, nickname in reversed(messages):
        avatar_url = get_avatar_url(db, msg.user_id, msg.detected_emotion)
        result.append({
            "user_id": msg.user_id,
            "nickname": nickname,
            "content": msg.content,
            "emotion": msg.detected_emotion,
            "avatar": avatar_url,
        })
    return result


def get_conversation_participants(db: Session, conversation_id: int) -> List[int]:
    """获取对话参与者ID列表"""
    participants = db.query(models.ConversationParticipant).filter(
        models.ConversationParticipant.conversation_id == conversation_id
    ).all()
    return [p.user_id for p in participants]


def set_conversation_agent(db: Session, conversation_id: int, active: bool):
    """设置对话的 Agent 状态"""
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if conv:
        conv.agent_active = active
        db.commit()
    return conv


def count_user_messages_in_conversation(db: Session, user_id: int, conversation_id: Optional[int] = None) -> int:
    """统计用户在指定对话中的消息数（conversation_id=None 表示全局消息）"""
    query = db.query(models.Message).filter(models.Message.user_id == user_id)
    if conversation_id is not None:
        query = query.filter(models.Message.conversation_id == conversation_id)
    else:
        query = query.filter(models.Message.conversation_id.is_(None))
    return query.count()


# 消息相关 (Messages)
def create_message(db: Session, user_id: int, content: str, emotion: str, conversation_id: Optional[int] = None):
    """保存消息，conversation_id=None 表示全局广播消息"""
    db_message = models.Message(
        user_id=user_id,
        content=content,
        detected_emotion=emotion,
        conversation_id=conversation_id,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_recent_messages_for_agent(db: Session, limit: int = 10, conversation_id: Optional[int] = None) -> List[Dict]:
    """获取最近 N 条消息，格式化为 Agent 可读格式"""
    query = db.query(models.Message, models.User.nickname).join(
        models.User, models.Message.user_id == models.User.id
    )
    if conversation_id is not None:
        query = query.filter(models.Message.conversation_id == conversation_id)
    else:
        query = query.filter(models.Message.conversation_id.is_(None))

    messages = query.order_by(models.Message.timestamp.desc()).limit(limit).all()

    history = []
    for msg, nickname in reversed(messages):
        history.append({"nickname": nickname, "content": msg.content})
    return history


def get_recent_messages_with_avatar(db: Session, limit: int = 50) -> List[Dict]:
    """获取最近 N 条全局消息，带头像 URL"""
    messages = db.query(models.Message, models.User.nickname).join(
        models.User, models.Message.user_id == models.User.id
    ).filter(
        models.Message.conversation_id.is_(None)
    ).order_by(models.Message.timestamp.desc()).limit(limit).all()

    result = []
    for msg, nickname in reversed(messages):
        avatar_url = get_avatar_url(db, msg.user_id, msg.detected_emotion)
        result.append({
            "user_id": msg.user_id,
            "nickname": nickname,
            "content": msg.content,
            "emotion": msg.detected_emotion,
            "avatar": avatar_url,
        })
    return result