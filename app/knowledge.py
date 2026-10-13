"""Source documents -> chunks -> persistent vector index -> cited evidence."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from app.config import Settings
from app.documents import load_documents, make_chunks

FAQ_PATH = Path(__file__).parent / "data" / "faq.json"


def split_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    return [text[i:i + size] for i in range(0, len(text), size - overlap)]


def tokens(text: str) -> Counter:
    parts = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text.lower())
    return Counter(t for part in parts for t in ([part] if part.isascii() or len(part) < 2 else
                   [part[i:i+2] for i in range(len(part)-1)]))


def cosine(a: Counter, b: Counter) -> float:
    divisor = math.sqrt(sum(x*x for x in a.values()) * sum(x*x for x in b.values()))
    return sum(v*b[k] for k, v in a.items()) / divisor if divisor else 0.0


class Knowledge:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.collection = None
        self.faq, self.documents = [], []
        if settings.knowledge_source == "faq":
            self.faq = json.loads(FAQ_PATH.read_text(encoding="utf-8"))
            self.chunks = [{"id": r["id"], "doc_id": r["id"], "source": r["source"],
                "title": r["question"], "section": "FAQ fixture", "url": "", "upstream_url": "",
                "path": "app/data/faq.json", "revision": "fixture", "line_start": 0, "line_end": 0,
                "answer": r["answer"], "embedding_text": r["question"] + " " + r["keywords"] + "\n" + r["answer"]}
                for r in self.faq]
        else:
            self.documents = load_documents(settings.knowledge_dir)
            self.chunks = make_chunks(self.documents, settings.chunk_size, settings.chunk_overlap)
        if not self.chunks:
            raise ValueError("知识库为空，请把 Markdown/TXT 放入 knowledge/zulip/documents 后重建索引。")
        self.by_id = {x["id"]: x for x in self.chunks}
        content = {"model": settings.embedding_model, "chunks": self.chunks, "format_version": 2}
        self.fingerprint = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
        self.indexed_now = 0
        if settings.retrieval_mode == "chroma":
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            embedding = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model,
                device="cpu", normalize_embeddings=True, cache_folder=str(settings.embedding_cache_path))
            client = chromadb.PersistentClient(path=str(settings.chroma_path))
            self.collection = client.get_or_create_collection("documents_" + self.fingerprint,
                embedding_function=embedding, metadata={"hnsw:space": "cosine"})
            existing = set(self.collection.get(include=[])["ids"])
            missing = [x for x in self.chunks if x["id"] not in existing]
            # Small CPU batches keep BGE-M3 memory use bounded on a 16 GB laptop.
            for i in range(0, len(missing), 8):
                batch = missing[i:i+8]
                self.collection.upsert(ids=[x["id"] for x in batch], documents=[x["embedding_text"] for x in batch],
                    metadatas=[{"doc_id": x["doc_id"], "section": x["section"]} for x in batch])
                self.indexed_now += len(batch)
                print(f"Indexed {self.indexed_now}/{len(missing)} new chunks", flush=True)
            if self.collection.count() != len(self.chunks):
                raise RuntimeError("索引与文档清单不一致，请检查知识库。")

    def search(self, query: str, k: int = 5, threshold: float | None = None) -> list[dict]:
        if k < 1:
            return []
        cutoff = self.settings.retrieval_threshold if threshold is None else threshold
        if self.collection is not None:
            result = self.collection.query(query_texts=[query], n_results=min(k * 4, len(self.chunks)), include=["distances"])
            hits = [{**self.by_id[chunk_id], "score": round(max(0.0, min(1.0, 1-distance)), 4)}
                    for chunk_id, distance in zip(result["ids"][0], result["distances"][0])]
        else:
            q = tokens(query)
            hits = [{**x, "score": round(cosine(q, tokens(x["embedding_text"])), 4)} for x in self.chunks]
            hits.sort(key=lambda x: x["score"], reverse=True)
        selected, counts = [], Counter()
        for hit in hits:
            if hit["score"] < cutoff or counts[hit["doc_id"]] >= 2:
                continue
            selected.append(hit)
            counts[hit["doc_id"]] += 1
            if len(selected) == k:
                break
        return selected

    def inventory(self) -> dict:
        return {"source": self.settings.knowledge_source, "document_count": len(self.documents),
                "chunk_count": len(self.chunks), "index_fingerprint": self.fingerprint,
                "documents": [{k: d[k] for k in ("id", "title", "path", "url", "upstream_url", "revision",
                            "license", "sha256", "modified_locally")} for d in self.documents]}
