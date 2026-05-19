import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, WebSocket, Query

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), '.env')
load_dotenv(env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY 未设置！请在 backend/.env 文件中配置 SECRET_KEY=<your-secret>")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: int, nickname: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "nickname": nickname,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": int(payload["sub"]), "nickname": payload.get("nickname", "")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


async def verify_ws_token(websocket: WebSocket, user_id: int, token: str = Query(...)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = int(payload["sub"])
        if token_user_id != user_id:
            await websocket.close(code=4003, reason="Token 与 user_id 不匹配")
            raise HTTPException(status_code=403, detail="身份不匹配")
        return token_user_id
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token 已过期")
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="无效的 Token")
        raise HTTPException(status_code=401, detail="无效的 Token")
