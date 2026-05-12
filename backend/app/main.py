# backend/app/main.py
import os
import shutil
import asyncio
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 导入模块
from . import models, crud, database, agent

# 初始化 App
app = FastAPI()

# 挂载静态文件目录 (用于访问头像图片)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)

# 挂载后，访问 http://IP:8000/static/avatars/xxx.png 即可看到图片
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict, exclude: WebSocket = None):
        """向所有在线用户广播，可选排除指定连接"""
        for connection in self.active_connections:
            if connection != exclude:
                await connection.send_json(message)


manager = ConnectionManager()


# 依赖注入：获取 DB 会话
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(nickname: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    如果是新用户 -> 注册
    如果是老用户 -> 验证密码并登录
    """
    if not password or not password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")

    user = crud.get_user_by_nickname(db, nickname)

    if user:
        # --- 登录逻辑 ---
        if user.password == password:
            return user
        else:
            raise HTTPException(status_code=400, detail="密码错误，无法登录")
    else:
        # --- 注册逻辑 ---
        return crud.create_user(db, nickname, password, "0.0.0.0")


@app.post("/upload_avatar")
async def upload_avatar(
        user_id: int = Form(...),
        emotion: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """用户上传带情绪标签的头像"""
    # 校验文件类型
    allowed_types = ["image/png", "image/jpeg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 PNG/JPG/GIF 格式的图片")

    # 校验文件大小 (5MB)
    max_size = 5 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    # 保存文件
    file_extension = file.filename.split(".")[-1].lower()
    filename = f"u{user_id}_{emotion}.{file_extension}"
    file_path = os.path.join(static_dir, "avatars", filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    web_path = f"/static/avatars/{filename}"

    # 写入数据库
    crud.create_avatar(db, user_id, web_path, emotion)

    return {"status": "success", "url": web_path}


@app.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """获取历史聊天记录 (用于前端初始化)"""
    messages = crud.get_recent_messages_with_avatar(db, limit=limit)
    return messages


# ===========================
# 核心：WebSocket 聊天逻辑
# ===========================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            # 接收前端发来的消息
            data = await websocket.receive_json()
            content = data.get("content")

            if not content:
                continue

            # 获取历史上下文 (前10句)
            history = crud.get_recent_messages_for_agent(db, limit=10)

            # 异步调用 AI Agent 分析情绪（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            current_emotion = await loop.run_in_executor(
                None, agent.analyze_emotion, history, content
            )

            # 保存消息到数据库
            crud.create_message(db, user_id, content, current_emotion)

            # 获取该用户对应情绪的头像
            avatar_url = crud.get_avatar_url(db, user_id, current_emotion)

            # 获取用户昵称
            user = db.query(models.User).filter(models.User.id == user_id).first()
            nickname = user.nickname if user else "未知用户"

            response_data = {
                "user_id": user_id,
                "nickname": nickname,
                "content": content,
                "emotion": current_emotion,
                "avatar": avatar_url
            }

            # 广播给其他人
            await manager.broadcast(response_data, exclude=websocket)
            # 单独发回给发送者（携带 AI 分析结果）
            await websocket.send_json(response_data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
