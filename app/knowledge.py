"""Offline lexical demo; optional persistent Chroma + BGE semantic retrieval."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from app.config import Settings


FAQ_PATH = Path(__file__).parent / "data" / "faq.json"


def split_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    return [text[i:i + size] for i in range(0, len(text), size - overlap)]


def tokens(text: str) -> Counter:
    parts = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text.lower())
    return Counter(t for part in parts for t in
                   ([part] if part.isascii() or len(part) < 2 else
                    [part[i:i+2] for i in range(len(part)-1)]))


def cosine(a: Counter, b: Counter) -> float:
    divisor = math.sqrt(sum(x*x for x in a.values()) * sum(x*x for x in b.values()))
    return sum(v*b[k] for k, v in a.items()) / divisor if divisor else 0.0


class Knowledge:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.faq = json.loads(FAQ_PATH.read_text(encoding="utf-8"))
        self.collection = None
        if settings.retrieval_mode == "chroma":
            # Explicit opt-in: model download is never triggered in offline mode.
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            embedding = SentenceTransformerEmbeddingFunction(
                model_name=settings.embedding_model, device="cpu", normalize_embeddings=True)
            client = chromadb.PersistentClient(path=str(settings.chroma_path))
            fingerprint = hashlib.sha256((settings.embedding_model + FAQ_PATH.read_text(
                encoding="utf-8")).encode()).hexdigest()[:16]
            self.collection = client.get_or_create_collection(
                "faq_" + fingerprint, embedding_function=embedding,
                metadata={"hnsw:space": "cosine"})
            if self.collection.count() == 0:
                ids, docs, meta = [], [], []
                for row in self.faq:
                    for i, chunk in enumerate(split_text(row["question"] + "\n" + row["answer"])):
                        ids.append(f"{row['id']}-{i}")
                        docs.append(chunk)
                        meta.append({"faq_id": row["id"], "source": row["source"],
                                     "answer": row["answer"]})
                self.collection.upsert(ids=ids, documents=docs, metadatas=meta)

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self.collection is not None:
            result = self.collection.query(query_texts=[query], n_results=min(k, self.collection.count()),
                                           include=["metadatas", "distances"])
            hits = [{"id": meta["faq_id"], "source": meta["source"], "answer": meta["answer"],
                     "score": round(max(0.0, min(1.0, 1-distance)), 4)}
                    for meta, distance in zip(result["metadatas"][0], result["distances"][0])]
        else:
            q = tokens(query)
            hits = [{"id": row["id"], "source": row["source"], "answer": row["answer"],
                     "score": round(cosine(q, tokens(row["question"] + " " + row["keywords"])), 4)}
                    for row in self.faq]
            hits.sort(key=lambda x: x["score"], reverse=True)
            hits = hits[:k]
        return [hit for hit in hits if hit["score"] >= self.settings.retrieval_threshold]
