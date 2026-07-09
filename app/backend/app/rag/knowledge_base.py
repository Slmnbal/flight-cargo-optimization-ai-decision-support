"""
RAG (Retrieval-Augmented Generation) katmanı: docs/business_rules.md ve
docs/adr/*.md içeriğini embed edip Chroma'da (yerel, dosya tabanlı bir vektör
veritabanı) saklar, sorgu zamanında en alakalı parçaları getirir.

Bu modül ml/demand_forecast.py'nin "artifact diske kalıcı olarak kaydedilir,
lazy yüklenir, python -m ile ayrı çalıştırılabilir" desenini izliyor -- ingest
(python -m app.rag.ingest_docs) ile sorgu (search_knowledge_base) birbirinden
bağımsız iki adım, tıpkı ML'deki train/predict ayrımı gibi.

Embedding kaynağı olarak Gemini'nin embed_content API'si kullanılıyor (zaten
kurulu google-generativeai paketi üzerinden) -- sentence-transformers gibi
yerel bir alternatif torch gibi ağır bir bağımlılık eklerdi, bu proje zaten
Gemini'ye bağımlı olduğu için ek bir risk oluşturmuyor.
"""
from pathlib import Path

import chromadb
import google.generativeai as genai

from app.config import settings

STORE_PATH = Path(__file__).parent / "store"
COLLECTION_NAME = "business_rules"
EMBEDDING_MODEL = "models/gemini-embedding-001"

_client = None


def _get_collection():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(STORE_PATH))
    return _client.get_or_create_collection(COLLECTION_NAME)


def _embed(text: str, task_type: str) -> list[float]:
    """
    task_type Gemini'ye embedding'in ne amaçla kullanılacağını söylüyor --
    "retrieval_document" (ingest sırasında, saklanacak metin için) ve
    "retrieval_query" (arama sırasında, kullanıcı sorusu için) farklı
    optimize edilmiş vektörler üretir; ikisini karıştırmak arama kalitesini
    düşürür.
    """
    genai.configure(api_key=settings.gemini_api_key)
    result = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type=task_type)
    return result["embedding"]


def upsert_chunks(chunks: list[str], ids: list[str], metadatas: list[dict]) -> None:
    """Ingest adımı: verilen metin parçalarını embed edip koleksiyona yazar/günceller."""
    if not chunks:
        return
    embeddings = [_embed(chunk, task_type="retrieval_document") for chunk in chunks]
    _get_collection().upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def search_knowledge_base(query: str, n_results: int = 3) -> list[str]:
    """Sorguya semantik olarak en yakın dokümantasyon parçalarını döndürür."""
    query_embedding = _embed(query, task_type="retrieval_query")
    result = _get_collection().query(query_embeddings=[query_embedding], n_results=n_results)
    # "documents" alanı [[chunk1, chunk2, ...]] şeklinde -- dış liste her sorgu
    # için bir sonuç listesi tutar; tek sorgu gönderdiğimiz için ilk elemanı alıyoruz.
    return result["documents"][0] if result["documents"] else []
