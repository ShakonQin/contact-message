import os
import shutil
import asyncio
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, Form, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, crud, database, agent
from .auth import create_access_token, verify_token, verify_ws_token

app = FastAPI()

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_USER_ID = 0


class ConnectionManager:
    def __init__(self):
        self.user_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.user_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.user_connections.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.user_connections

    async def send_to_user(self, user_id: int, message: dict):
        ws = self.user_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id)

    async def broadcast_global(self, message: dict, exclude_user_id: int = None):
        for uid, ws in list(self.user_connections.items()):
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(uid)

    async def broadcast_to_conversation(self, conversation_id: int, message: dict, db: Session, exclude_user_id: int = None):
        participant_ids = crud.get_conversation_participants(db, conversation_id)
        for uid in participant_ids:
            if uid == exclude_user_id:
                continue
            await self.send_to_user(uid, message)


manager = ConnectionManager()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(token: str = Query(..., alias="token"), db: Session = Depends(get_db)) -> int:
    payload = verify_token(token)
    return payload["user_id"]


@app.on_event("startup")
def startup_event():
    """启动时创建 Agent 用户（如果不存在）"""
    db = database.SessionLocal()
    try:
        agent_user = db.query(models.User).filter(models.User.id == AGENT_USER_ID).first()
        if not agent_user:
            agent_user = models.User(
                id=AGENT_USER_ID,
                nickname="AI助手",
                password=crud.hash_password("agent_no_login"),
                ip_address="127.0.0.1",
            )
            db.add(agent_user)
            db.commit()
            print("已创建 AI助手 用户 (id=0)")
    finally:
        db.close()


@app.post("/register")
def register(nickname: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if not password or not password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")

    user = crud.get_user_by_nickname(db, nickname)

    if user:
        stored = user.password
        if stored.startswith("$2b$"):
            if not crud.verify_password(password, stored):
                raise HTTPException(status_code=400, detail="密码错误，无法登录")
        else:
            if stored != password:
                raise HTTPException(status_code=400, detail="密码错误，无法登录")
            user.password = crud.hash_password(password)
            db.commit()
    else:
        user = crud.create_user(db, nickname, password, "0.0.0.0")

    token = create_access_token(user.id, user.nickname)
    return {"user": user, "access_token": token}


@app.get("/users")
def get_users(token: str = Query(...), db: Session = Depends(get_db)):
    """获取所有用户列表（用于发起私聊）"""
    verify_token(token)
    users = crud.get_all_users(db)
    return [{"id": u.id, "nickname": u.nickname} for u in users if u.id != AGENT_USER_ID]


@app.post("/upload_avatar")
async def upload_avatar(
        user_id: int = Form(...),
        emotion: str = Form(...),
        file: UploadFile = File(...),
        token: str = Form(...),
        db: Session = Depends(get_db)
):
    payload = verify_token(token)
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权操作此用户")

    allowed_types = ["image/png", "image/jpeg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 PNG/JPG/GIF 格式的图片")

    max_size = 5 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    file_extension = file.filename.split(".")[-1].lower()
    filename = f"u{user_id}_{emotion}.{file_extension}"
    file_path = os.path.join(static_dir, "avatars", filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    web_path = f"/static/avatars/{filename}"
    crud.create_avatar(db, user_id, web_path, emotion)
    return {"status": "success", "url": web_path}


@app.get("/history")
def get_history(token: str = Query(...), limit: int = 50, db: Session = Depends(get_db)):
    verify_token(token)
    messages = crud.get_recent_messages_with_avatar(db, limit=limit)
    return messages


# ==================== 对话相关接口 ====================

@app.post("/conversations")
def create_conversation(target_user_id: int = Body(..., embed=True), token: str = Query(...), db: Session = Depends(get_db)):
    """创建或获取与目标用户的私聊对话"""
    payload = verify_token(token)
    user_id = payload["user_id"]
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="不能和自己私聊")
    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    conv = crud.get_or_create_dm_conversation(db, user_id, target_user_id)
    return {"conversation_id": conv.id, "agent_active": conv.agent_active}


@app.get("/conversations")
def list_conversations(token: str = Query(...), db: Session = Depends(get_db)):
    """获取当前用户的所有对话"""
    payload = verify_token(token)
    conversations = crud.get_user_conversations(db, payload["user_id"])
    return conversations


@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, token: str = Query(...), limit: int = 50, db: Session = Depends(get_db)):
    """获取对话中的消息"""
    payload = verify_token(token)
    user_id = payload["user_id"]
    participants = crud.get_conversation_participants(db, conversation_id)
    if user_id not in participants and user_id != AGENT_USER_ID:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    messages = crud.get_conversation_messages(db, conversation_id, limit=limit)
    return messages


@app.post("/conversations/{conversation_id}/agent")
def toggle_agent(conversation_id: int, active: bool = Body(..., embed=True), token: str = Query(...), db: Session = Depends(get_db)):
    """启用/禁用对话中的聊天 Agent"""
    payload = verify_token(token)
    user_id = payload["user_id"]
    participants = crud.get_conversation_participants(db, conversation_id)
    if user_id not in participants:
        raise HTTPException(status_code=403, detail="无权操作此对话")
    conv = crud.set_conversation_agent(db, conversation_id, active)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"conversation_id": conv.id, "agent_active": conv.agent_active}


# ==================== WebSocket ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = Query(...)):
    try:
        await verify_ws_token(websocket, user_id, token)
    except HTTPException:
        return

    await manager.connect(websocket, user_id)
    db = database.SessionLocal()

    # 广播用户加入通知
    user = db.query(models.User).filter(models.User.id == user_id).first()
    nickname = user.nickname if user else "未知用户"
    await manager.broadcast_global(
        {"type": "system", "content": f"{nickname} 加入了聊天室", "online_count": len(manager.user_connections)},
        exclude_user_id=user_id,
    )

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            conversation_id = data.get("conversation_id")  # None = 全局广播

            if not content:
                continue

            # 情绪分析
            history = crud.get_recent_messages_for_agent(db, limit=10, conversation_id=conversation_id)
            loop = asyncio.get_event_loop()
            current_emotion = await loop.run_in_executor(None, agent.analyze_emotion, history, content)

            # 保存消息
            crud.create_message(db, user_id, content, current_emotion, conversation_id)

            avatar_url = crud.get_avatar_url(db, user_id, current_emotion)
            user = db.query(models.User).filter(models.User.id == user_id).first()
            nickname = user.nickname if user else "未知用户"

            response_data = {
                "user_id": user_id,
                "nickname": nickname,
                "content": content,
                "emotion": current_emotion,
                "avatar": avatar_url,
                "conversation_id": conversation_id,
            }

            # 广播消息
            if conversation_id:
                await manager.broadcast_to_conversation(conversation_id, response_data, db)
            else:
                await manager.broadcast_global(response_data)

            # 检查是否需要触发总结 Agent（每 10 条消息）
            msg_count = crud.count_user_messages_in_conversation(db, user_id, conversation_id)
            if msg_count % 10 == 0 and msg_count > 0:
                asyncio.create_task(_run_summary_agent(db, user_id, nickname, conversation_id))

            # 检查是否需要聊天 Agent 回复
            trigger_content = content
            if conversation_id:
                conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
                agent_should_respond = conv and conv.agent_active
            else:
                # 群聊：仅响应 @robot / @ai 前缀的消息
                stripped = content.strip().lower()
                if stripped.startswith("@robot"):
                    agent_should_respond = True
                    trigger_content = content.strip()[6:].strip()
                elif stripped.startswith("@ai"):
                    agent_should_respond = True
                    trigger_content = content.strip()[3:].strip()
                else:
                    agent_should_respond = False

            if agent_should_respond and trigger_content:
                asyncio.create_task(
                    _run_chat_agent(db, user_id, nickname, conversation_id, trigger_content)
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast_global(
            {"type": "system", "content": f"{nickname} 离开了聊天室", "online_count": len(manager.user_connections)},
        )
    finally:
        db.close()


async def _run_summary_agent(db: Session, user_id: int, nickname: str, conversation_id: Optional[int]):
    """后台运行总结 Agent"""
    try:
        from . import summary_agent
        recent = crud.get_recent_messages_for_agent(db, limit=20, conversation_id=conversation_id)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, summary_agent.summarize_user, user_id, nickname, recent)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"总结 Agent 失败: {e}")


async def _run_chat_agent(db: Session, trigger_user_id: int, trigger_nickname: str, conversation_id: Optional[int], trigger_content: str):
    """后台运行聊天 Agent，生成回复并广播"""
    try:
        from . import chat_agent
        recent = crud.get_recent_messages_for_agent(db, limit=10, conversation_id=conversation_id)
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None, chat_agent.generate_response, trigger_user_id, trigger_nickname, recent, conversation_id
        )

        if not chunks:
            return

        for chunk in chunks:
            if not chunk.strip():
                continue
            emotion = await loop.run_in_executor(None, agent.analyze_emotion, [], chunk)
            crud.create_message(db, AGENT_USER_ID, chunk, emotion, conversation_id)
            avatar_url = crud.get_avatar_url(db, AGENT_USER_ID, emotion)
            response_data = {
                "user_id": AGENT_USER_ID,
                "nickname": "AI助手",
                "content": chunk,
                "emotion": emotion,
                "avatar": avatar_url,
                "conversation_id": conversation_id,
            }
            if conversation_id:
                await manager.broadcast_to_conversation(conversation_id, response_data, db)
            else:
                await manager.broadcast_global(response_data)
            await asyncio.sleep(0.5)  # 模拟打字间隔

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"聊天 Agent 失败: {e}")
