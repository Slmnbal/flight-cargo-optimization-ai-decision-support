"""
docs/business_rules.md ve docs/adr/*.md dosyalarını okuyup, Chroma'ya embed
edilmiş chunk'lar olarak yükler. Çalıştırmak için: python -m app.rag.ingest_docs

Chunking stratejisi: her dosyayı "## " (H2) başlıklarından böler -- bir bölüm
(örn. "## Karar 1 — Embargo kapsamı") tek bir chunk olur. Bu, cümle ortasından
rastgele kesmek yerine doğal anlamsal sınırlarda bölmeyi sağlıyor. Gerçek RAG
sistemleri genelde token sayısına göre de böler ve chunk'lar arasında overlap
bırakır (bir cümle iki chunk arasında bölünürse bağlam kaybolmasın diye) --
burada buna ihtiyaç yok çünkü kaynak dosyalar küçük, elle yazılmış ve zaten
başlıklarla iyi bölümlenmiş dokümantasyon; overlap, birbirini tekrar eden
gereksiz chunk'lar üretirdi.

Not (bilinen sınırlama): bu script docs/ klasörünü repo kökünden okuyor.
Dockerfile şu an sadece backend/app ve backend/alembic'i image'a kopyalıyor,
docs/ klasörünü değil -- yani ingest, konteyner içinde değil yerelde
çalıştırılmalı (python -m app.rag.ingest_docs), üretilen store/ klasörü
(gitignored) sonra imaja dahil edilebilir. Docker build context'ini repo
köküne genişletmek bu sınırlamayı kaldırır ama bu projenin şu anki kapsamının
dışında bırakıldı.
"""
from pathlib import Path

from app.rag.knowledge_base import upsert_chunks

DOCS_ROOT = Path(__file__).resolve().parents[4] / "docs"
SOURCE_FILES = [
    DOCS_ROOT / "business_rules.md",
    DOCS_ROOT / "adr" / "0001-cargo-optimization-constraints.md",
    DOCS_ROOT / "adr" / "0002-postgresql-migration.md",
]


def _split_into_chunks(text: str) -> list[str]:
    sections = text.split("\n## ")
    chunks = [sections[0].strip()] if sections[0].strip() else []
    chunks += [("## " + section).strip() for section in sections[1:]]
    return [c for c in chunks if c]


def ingest():
    chunks, ids, metadatas = [], [], []
    for path in SOURCE_FILES:
        if not path.exists():
            print(f"Atlanıyor (bulunamadı): {path}")
            continue
        for i, chunk in enumerate(_split_into_chunks(path.read_text(encoding="utf-8"))):
            chunks.append(chunk)
            ids.append(f"{path.stem}-{i}")
            metadatas.append({"source": path.name})

    upsert_chunks(chunks, ids, metadatas)
    print(f"RAG ingest tamamlandı: {len(chunks)} chunk, {len(SOURCE_FILES)} kaynak dosya taranmış.")


if __name__ == "__main__":
    ingest()
