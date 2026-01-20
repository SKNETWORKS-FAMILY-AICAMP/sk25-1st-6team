from sqlalchemy import Column, String
from app.core.database import Base

class Sido(Base):
    __tablename__ = "regions"  # <-- 실제 테이블명으로 수정

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(50), nullable=False)