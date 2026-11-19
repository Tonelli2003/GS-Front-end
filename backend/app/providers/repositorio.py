"""Persistência simples em SQLite (adequada para a POC). Guarda o protocolo como JSON."""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.schemas.relato import Protocolo

_lock = threading.Lock()


class Repositorio:
    def __init__(self, caminho: str) -> None:
        if caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(caminho, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS protocolos ("
            " numero TEXT PRIMARY KEY, criado_em TEXT NOT NULL, dados TEXT NOT NULL)"
        )
        self.conn.commit()

    def proximo_numero(self) -> str:
        ano = datetime.now(timezone.utc).year
        with _lock:
            (qtd,) = self.conn.execute(
                "SELECT COUNT(*) FROM protocolos WHERE numero LIKE ?", (f"BED-{ano}-%",)
            ).fetchone()
        return f"BED-{ano}-{qtd + 1:06d}"

    def salvar(self, p: Protocolo) -> Protocolo:
        with _lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO protocolos (numero, criado_em, dados) VALUES (?, ?, ?)",
                (p.numero, p.criado_em.isoformat(), p.model_dump_json()),
            )
            self.conn.commit()
        return p

    def obter(self, numero: str) -> Protocolo | None:
        with _lock:
            linha = self.conn.execute(
                "SELECT dados FROM protocolos WHERE numero = ?", (numero.upper(),)
            ).fetchone()
        return Protocolo.model_validate(json.loads(linha[0])) if linha else None

    def listar(self) -> list[Protocolo]:
        with _lock:
            linhas = self.conn.execute(
                "SELECT dados FROM protocolos ORDER BY criado_em DESC"
            ).fetchall()
        return [Protocolo.model_validate(json.loads(l[0])) for l in linhas]

    def contar(self) -> int:
        with _lock:
            return self.conn.execute("SELECT COUNT(*) FROM protocolos").fetchone()[0]


@lru_cache
def _repo_singleton() -> Repositorio:
    return Repositorio(get_settings().db_path)


def get_repositorio() -> Repositorio:
    return _repo_singleton()
