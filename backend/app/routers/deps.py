"""Dependências compartilhadas entre routers."""
import secrets

from fastapi import Header, HTTPException

from app.config import get_settings


def exigir_gestor(x_gestor_token: str | None = Header(default=None)) -> None:
    """RBAC simples para a POC: rotas de gestor exigem o token do .env."""
    esperado = get_settings().gestor_token
    if not esperado or not x_gestor_token or not secrets.compare_digest(x_gestor_token, esperado):
        raise HTTPException(status_code=401, detail="Acesso restrito a gestores.")
