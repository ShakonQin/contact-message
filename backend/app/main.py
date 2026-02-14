# backend/app/main.py
import os
import shutil
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 导入我们可以信任的模块
from . import models, crud, database, agent

# 初始化 App
app = FastAPI()

# 挂载静态文件目录 (用于访问头像图片)
# 确保 backend/static 目录存在
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)

# 挂载后，访问 http://IP:8000/static/avatars/xxx.png 即可看到图片
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 3. CORS 设置 (允许前端跨域访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 局域网开发建议允许所有
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        # 存放所有活跃的 websocket 连接
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # 向所有在线用户广播 JSON 数据
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()



# API 路由
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
    # 查找是否存在该昵称
    user = crud.get_user_by_nickname(db, nickname)

    if user:
        # --- 登录逻辑 ---
        # 简单验证密码
        if user.password == password:
            return user
        else:
            raise HTTPException(status_code=400, detail="密码错误，无法登录")
    else:
        # --- 注册逻辑 ---
        # 获取请求来源 IP (用于局域网识别)
        # 这里为了简单直接写 0.0.0.0，如果想记录真实IP，可以使用 request.client.host
        return crud.create_user(db, nickname, password, "0.0.0.0")



@app.post("/upload_avatar")
async def upload_avatar(
        user_id: int = Form(...),
        emotion: str = Form(...),  # happy, sad, etc.
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """用户上传带情绪标签的头像"""
    # 保存文件
    file_extension = file.filename.split(".")[-1]
    filename = f"u{user_id}_{emotion}.{file_extension}"
    file_path = os.path.join(static_dir, "avatars", filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 生成 Web 访问路径
    web_path = f"/static/avatars/{filename}"

    # 写入数据库
    crud.create_avatar(db, user_id, web_path, emotion)

    return {"status": "success", "url": web_path}


@app.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """获取历史聊天记录 (用于前端初始化)"""
    # 这里偷个懒，直接用 crud 里的函数
    # 注意：这里返回的数据需要包含头像 URL，稍微复杂一点，暂且略过，
    # 真正的实时逻辑在下面的 WebSocket 中。
    pass


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
            # 预期格式: {"content": "你好"}
            content = data.get("content")

            if not content:
                continue

            # 获取历史上下文 (前10句)
            # 使用我们刚写的 crud.py
            history = crud.get_recent_messages_for_agent(db, limit=10)

            # 调用 AI Agent 分析情绪
            # 这一步可能会有延迟，生产环境建议放入后台任务，但 Demo 可以直接 await
            # 注意 agent.analyze_emotion 是同步函数，可以直接调用
            # 如果觉得卡顿，可以使用 run_in_executor
            current_emotion = agent.analyze_emotion(history, content)

            # 保存消息到数据库
            crud.create_message(db, user_id, content, current_emotion)

            # 获取该用户对应情绪的头像
            avatar_url = crud.get_avatar_url(db, user_id, current_emotion)

            #  获取用户昵称 (为了广播)
            user = db.query(models.User).filter(models.User.id == user_id).first()
            nickname = user.nickname if user else "未知用户"

            # 广播给所有人
            response_data = {
                "user_id": user_id,
                "nickname": nickname,
                "content": content,
                "emotion": current_emotion,  # 让前端也能看到 AI 判断的情绪
                "avatar": avatar_url  # 动态变化的头像 URL
            }

            await manager.broadcast(response_data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # 可选：广播 "某某离开了"