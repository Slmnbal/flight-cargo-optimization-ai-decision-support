"""
Agent'ın konuşma hafızasını yöneten servis katmanı. api/routes.py sadece HTTP
katmanı (request/response), agents/explainer.py sadece Gemini ile konuşma mantığı --
"bir konuşmanın mesajlarını nasıl saklayıp geri yüklüyoruz" sorusu ise ne HTTP'ye ne
de LLM çağrısına ait, bu yüzden kendi servis modülünde (dev_principles_guide.md §3'te
tanımlanan services/ sorumluluğu).
"""
import uuid

from sqlalchemy.orm import Session

from app.models import AgentMessage

MAX_HISTORY_MESSAGES = 20


def new_session_id() -> str:
    return uuid.uuid4().hex


def save_message(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(AgentMessage(session_id=session_id, role=role, content=content))
    db.commit()


def load_conversation_history(db: Session, session_id: str, max_messages: int = MAX_HISTORY_MESSAGES) -> list[dict]:
    """
    Gemini'nin start_chat(history=...) parametresinin beklediği formatta
    ([{"role": "user"/"model", "parts": [...]}, ...]) bu session_id'ye ait son
    max_messages mesajı, KRONOLOJİK sırada döndürür.
    """
    # message_id'yi ikincil sıralama anahtarı olarak ekliyoruz: created_at tek
    # başına aynı milisaniyede yazılan mesajlar arasında kararsız (unstable) bir
    # sıra üretebilir, autoincrement PK ise insertion sırasını garanti verir.
    recent_messages = (
        db.query(AgentMessage)
        .filter(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at.desc(), AgentMessage.message_id.desc())
        .limit(max_messages)
        .all()
    )
    # Sorgu en yeniden en eskiye döndü (son N mesajı almak için); Gemini'ye
    # vermeden önce kronolojik sıraya (en eski önce) çeviriyoruz -- aksi halde
    # model konuşmayı tersten okur.
    return [{"role": msg.role, "parts": [msg.content]} for msg in reversed(recent_messages)]
