"""Modelos do assistente de orientação ao cidadão."""
from typing import Literal

from pydantic import BaseModel, Field


class Mensagem(BaseModel):
    papel: Literal["cidadao", "assistente"]
    texto: str = Field(max_length=2000)


class PerguntaAssistente(BaseModel):
    pergunta: str = Field(min_length=3, max_length=800)
    historico: list[Mensagem] = Field(default_factory=list, max_length=10)
    cidade: str | None = Field(default=None, max_length=80)


class Canal(BaseModel):
    nome: str = Field(max_length=120)
    como_acessar: str = Field(max_length=200)
    quando_usar: str = Field(max_length=250)


class RespostaAssistente(BaseModel):
    """Saída estruturada do LLM para o assistente."""

    resposta: str = Field(min_length=5, max_length=1200, description="Resposta direta em linguagem simples")
    passos: list[str] = Field(default_factory=list, max_length=6, description="Passo a passo curto")
    canais: list[Canal] = Field(default_factory=list, max_length=4)
    emergencia: bool = Field(description="A situação envolve risco imediato à vida?")
    fora_do_escopo: bool = False
    aviso: str | None = Field(default=None, max_length=300)


class FeedbackAssistente(BaseModel):
    pergunta: str = Field(max_length=800)
    util: bool
