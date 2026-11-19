"""Configuração centralizada. Todos os segredos vêm de variáveis de ambiente / .env."""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.groq_vision_model: str = os.getenv(
            "GROQ_VISION_MODEL", "qwen/qwen3.8-27b"
        )
        self.groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
        self.llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "30"))
        # CORS restritivo: lista explícita de origens, nunca "*"
        self.allowed_origins: list[str] = [
            o.strip()
            for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
            if o.strip() and o.strip() != "*"
        ]
        self.gestor_token: str = os.getenv("GESTOR_TOKEN", "")
        self.db_path: str = os.getenv("DB_PATH", "data/bairro_em_dia.db")
        self.seed_demo: bool = os.getenv("SEED_DEMO", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
