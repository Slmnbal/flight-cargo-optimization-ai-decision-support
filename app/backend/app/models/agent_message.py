from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.connection import Base


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    # Aynı konuşmaya ait mesajları gruplamak için: bir kullanıcı oturumu, birden
    # fazla soru-cevap turu boyunca aynı session_id'yi taşır.
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" / "model"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
