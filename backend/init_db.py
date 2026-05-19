import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import text, inspect
from app.database import engine, SessionLocal, Base
from app import models


def init_db():
    print("正在初始化数据库...")

    # 创建所有新表
    Base.metadata.create_all(bind=engine)

    # 为已有的 messages 表添加 conversation_id 列（SQLite 不支持 IF NOT EXISTS，需要先检查）
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("messages")]
    if "conversation_id" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE messages ADD COLUMN conversation_id INTEGER REFERENCES conversations(id)"))
            conn.commit()
        print("已为 messages 表添加 conversation_id 列")

    print(f"数据库文件已生成，位置: {engine.url}")
    print("初始化完成！")


if __name__ == "__main__":
    init_db()