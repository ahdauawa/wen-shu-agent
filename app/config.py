from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WENSHU_", env_file=".env", extra="ignore")

    api_keys: SecretStr = SecretStr("")
    db_path: Path = Path("data/wenshu.sqlite3")
    model_mode: Literal["offline", "openai"] = "offline"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "deepseek-chat"
    llm_timeout: float = Field(default=20, gt=0, le=120)
    retrieval_mode: Literal["lexical", "chroma"] = "lexical"
    knowledge_source: Literal["documents", "faq"] = "documents"
    knowledge_dir: Path = Path("knowledge/zulip")
    chunk_size: int = Field(default=800, ge=100, le=2000)
    chunk_overlap: int = Field(default=100, ge=0)
    embedding_model: str = "BAAI/bge-m3"
    embedding_cache_path: Path = Path("data/models")
    chroma_path: Path = Path("data/chroma")
    retrieval_threshold: float = Field(default=0.18, ge=0, le=1)
    intent_threshold: float = Field(default=0.65, ge=0, le=1)

    @property
    def keys(self) -> list[str]:
        return [s.strip() for s in self.api_keys.get_secret_value().split(",") if s.strip()]

    @model_validator(mode="after")
    def check_remote_model(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.model_mode == "openai" and not self.llm_api_key.get_secret_value():
            raise ValueError("openai 模式必须设置 WENSHU_LLM_API_KEY")
        return self
