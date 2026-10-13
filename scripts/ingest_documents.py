"""Build/reuse a content-addressed local index without calling an LLM."""
import json
from app.config import Settings
from app.knowledge import Knowledge

if __name__ == "__main__":
    knowledge = Knowledge(Settings(model_mode="offline", knowledge_source="documents", retrieval_mode="chroma"))
    print(json.dumps({k: v for k, v in knowledge.inventory().items() if k != "documents"}, indent=2))
    print("Newly indexed chunks:", knowledge.indexed_now)
