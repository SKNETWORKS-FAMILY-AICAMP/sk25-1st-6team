import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ backend/.env 파일을 정확히 지정해서 로드
ENV_PATH = Path(__file__).resolve().parents[3] / "backend" / ".env"
load_dotenv(ENV_PATH, override=True)

# 환경변수에서 DB 접속 정보 읽기
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# 🔎 로드 확인용 (성공 확인 후 삭제 가능)
print("ENV_PATH =", ENV_PATH)
print("DB_HOST loaded =", DB_HOST)

# MySQL 연결 URL
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# DB 세션 생성기
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ORM 베이스 클래스
Base = declarative_base()

# FastAPI에서 사용하는 DB 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()