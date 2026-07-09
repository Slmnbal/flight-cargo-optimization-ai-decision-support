"""
RAG retrieval pipeline'ının (embed -> Chroma'ya yaz -> sorgula -> chunk döndür)
uçtan uca çalıştığını, gerçek Gemini API'sine bağımlı OLMADAN test eder. Gerçek
embed_content çağrısı ağ + API key gerektirdiği için (mevcut test felsefesi dış
API'lere bağımlı test yazmamak), burada onu basit ama anlamlı bir "sahte" embedding
fonksiyonuyla (kelime sayımına dayalı bag-of-words vektörü) değiştiriyoruz -- amaç
Gemini'nin embedding kalitesini değil, ingest/query pipeline'ının doğru chunk'ı
doğru sorguya eşleştirdiğini test etmek.
"""
import chromadb
import pytest

from app.rag import knowledge_base

VOCAB = ["embargo", "priority", "soğuk", "zincir", "tehlikeli"]


def _fake_embed(text: str, task_type: str) -> list[float]:
    lowered = text.lower()
    return [float(lowered.count(word)) for word in VOCAB]


@pytest.fixture()
def isolated_knowledge_base(monkeypatch, tmp_path):
    """Gerçek store/ klasörü ve gerçek Gemini embedding'i yerine geçici/sahte olanları kullanır."""
    monkeypatch.setattr(knowledge_base, "_embed", _fake_embed)
    monkeypatch.setattr(knowledge_base, "_client", chromadb.PersistentClient(path=str(tmp_path)))
    yield


def test_search_knowledge_base_returns_most_relevant_chunk(isolated_knowledge_base):
    chunks = [
        "Embargo aktifken bazı kargo tipleri o rotada taşınamaz.",
        "Priority class contract kargoya korumalı kapasite ayırır.",
        "Soğuk zincir gerektiren kargo ayrı bir kapasiteyle sınırlıdır.",
    ]
    knowledge_base.upsert_chunks(chunks, ids=["c0", "c1", "c2"], metadatas=[{"source": "test"}] * 3)

    results = knowledge_base.search_knowledge_base("embargo ne demek", n_results=1)

    assert results == [chunks[0]]


def test_search_knowledge_base_respects_n_results(isolated_knowledge_base):
    chunks = [
        "Embargo aktifken bazı kargo tipleri o rotada taşınamaz.",
        "Priority class contract kargoya korumalı kapasite ayırır.",
        "Soğuk zincir gerektiren kargo ayrı bir kapasiteyle sınırlıdır.",
    ]
    knowledge_base.upsert_chunks(chunks, ids=["c0", "c1", "c2"], metadatas=[{"source": "test"}] * 3)

    results = knowledge_base.search_knowledge_base("soğuk zincir tehlikeli", n_results=2)

    assert len(results) == 2
