import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Windows 路径适配
current_dir = os.path.dirname(os.path.abspath(__file__))

backend_dir = os.path.dirname(current_dir)

# 拼接数据库文件的完整路径: .../backend/chat.db
db_path = os.path.join(backend_dir, "chat.db")

# SQLite 连接 URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"


# SQLAlchemy 核心设置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依赖注入函数 (供 FastAPI 使用)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()