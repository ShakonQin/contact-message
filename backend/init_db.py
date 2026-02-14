# backend/init_db.py
import sys
import os

# 将当前目录添加到 Python 路径
sys.path.append(os.getcwd())

from app.database import engine, Base
from app import models


def init_db():
    print("正在 Windows 环境下初始化数据库...")

    Base.metadata.create_all(bind=engine)

    print(f"数据库文件已生成，位置: {engine.url}")
    print("初始化完成！")


if __name__ == "__main__":
    init_db()