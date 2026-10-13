"""Local Markdown/TXT documents, deterministic chunks and source coordinates."""
import hashlib
import json
import re
from pathlib import Path


def load_documents(folder: Path) -> list[dict]:
    folder = folder.resolve()
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    listed = {row["path"]: row for row in manifest.get("documents", [])}
    documents = []
    for path in sorted((folder / "documents").rglob("*")):
        if path.suffix.lower() not in (".md", ".txt") or not path.is_file():
            continue
        if not path.resolve().is_relative_to(folder):
            raise ValueError("Document symlink escapes knowledge directory")
        if path.stat().st_size > 2_000_000:
            raise ValueError(f"Document exceeds 2 MB: {path.name}")
        relative = path.relative_to(folder).as_posix()
        row = listed.get(relative, {})
        body = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        title = row.get("title") or (heading[1] if heading else path.stem)
        doc_id = row.get("id") or "local-" + hashlib.sha256(relative.encode()).hexdigest()[:16]
        sha = hashlib.sha256(body.encode()).hexdigest()
        documents.append({"id": doc_id, "title": title, "text": body, "path": relative,
            "url": row.get("url", ""), "upstream_url": row.get("upstream_url", ""),
            "revision": row.get("revision", "local"), "license": row.get("license", "local"),
            "sha256": sha, "modified_locally": bool(row.get("sha256") and row["sha256"] != sha)})
    if len({d["id"] for d in documents}) != len(documents):
        raise ValueError("Duplicate document IDs")
    return documents


def make_chunks(documents: list[dict], size: int = 800, overlap: int = 100) -> list[dict]:
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    chunks = []
    for doc in documents:
        text = doc["text"]
        headings = list(re.finditer(r"^#{1,6}\s+(.+)$", text, re.M))
        boundaries = sorted(set([0, len(text)] + [m.start() for m in headings]))
        section = doc["title"]
        for begin, end in zip(boundaries, boundaries[1:]):
            section = next((m[1] for m in headings if m.start() == begin), section)
            start = begin
            while start < end:
                stop = min(start + size, end)
                if stop < end:
                    boundary = max(text.rfind("\n", start + size // 2, stop), text.rfind(" ", start + size // 2, stop))
                    if boundary > start:
                        stop = boundary
                excerpt = text[start:stop]
                if excerpt.strip():
                    chunks.append({"id": f"{doc['id']}:{start}-{stop}", "doc_id": doc["id"],
                        "title": doc["title"], "section": section, "source": f"{doc['title']} / {section}",
                        "url": doc["url"], "upstream_url": doc["upstream_url"], "revision": doc["revision"],
                        "path": doc["path"], "line_start": text.count("\n", 0, start) + 1,
                        "line_end": text.count("\n", 0, max(start, stop - 1)) + 1,
                        "char_start": start, "char_end": stop, "answer": excerpt,
                        "embedding_text": doc["title"] + "\n" + section + "\n" + excerpt})
                if stop == end:
                    break
                start = max(start + 1, stop - overlap)
    return chunks
