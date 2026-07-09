"""
Agent hafıza katmanının (save_message / load_conversation_history) veritabanı
seviyesinde doğru çalıştığını test eder -- gerçek bir Gemini çağrısı yapılmıyor,
mevcut test felsefesiyle tutarlı (dış API'lere bağımlı testler yazmıyoruz).
"""
from app.services.agent_service import load_conversation_history, save_message


def test_load_conversation_history_returns_chronological_gemini_format(db_session):
    save_message(db_session, "session-1", "user", "merhaba")
    save_message(db_session, "session-1", "model", "merhaba, nasıl yardımcı olabilirim?")
    save_message(db_session, "session-1", "user", "1 numaralı talep neden reddedildi?")

    history = load_conversation_history(db_session, "session-1")

    assert history == [
        {"role": "user", "parts": ["merhaba"]},
        {"role": "model", "parts": ["merhaba, nasıl yardımcı olabilirim?"]},
        {"role": "user", "parts": ["1 numaralı talep neden reddedildi?"]},
    ]


def test_load_conversation_history_respects_max_messages_and_stays_chronological(db_session):
    for i in range(5):
        save_message(db_session, "session-2", "user", f"soru {i}")

    history = load_conversation_history(db_session, "session-2", max_messages=2)

    # Son 2 mesaj alınmalı (soru 3, soru 4) ve kronolojik sırada olmalı.
    assert [h["parts"][0] for h in history] == ["soru 3", "soru 4"]


def test_load_conversation_history_isolates_sessions(db_session):
    save_message(db_session, "session-a", "user", "a-mesaji")
    save_message(db_session, "session-b", "user", "b-mesaji")

    history_a = load_conversation_history(db_session, "session-a")

    assert len(history_a) == 1
    assert history_a[0]["parts"] == ["a-mesaji"]
