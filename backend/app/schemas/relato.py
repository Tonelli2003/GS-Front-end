"""Modelos Pydantic de entrada e saída dos relatos (inclui a saída estruturada do LLM)."""
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_IMAGEM_B64 = 5_600_000  # ~4 MB de imagem em base64


class Categoria(str, Enum):
    BURACO = "buraco_via"
    ILUMINACAO = "iluminacao"
    LIXO = "lixo_entulho"
    RUIDO = "ruido"
    AGUA_ESGOTO = "agua_esgoto"
    ARVORE = "arvore_area_verde"
    CALCADA = "calcada_acessibilidade"
    OUTRO = "outro"


class Criticidade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class Status(str, Enum):
    RECEBIDO = "recebido"
    EM_ANALISE = "em_analise"
    ENCAMINHADO = "encaminhado"
    RESOLVIDO = "resolvido"
    RECUSADO = "recusado"


def _limpar(v: str | None) -> str | None:
    if v is None:
        return None
    v = " ".join(v.split())
    return v or None


class RelatoBase(BaseModel):
    descricao: str = Field(min_length=20, max_length=1500, description="O que está acontecendo")
    endereco: str = Field(min_length=5, max_length=200, description="Rua, número ou ponto de referência")
    bairro: str = Field(min_length=2, max_length=80)
    cidade: str = Field(default="São Paulo", min_length=2, max_length=80)
    cep: str | None = Field(default=None, pattern=r"^\d{5}-?\d{3}$")
    transcricao_audio: str | None = Field(default=None, max_length=3000)

    @field_validator("descricao", "endereco", "bairro", "cidade", "transcricao_audio", mode="before")
    @classmethod
    def normalizar(cls, v):
        return _limpar(v) if isinstance(v, str) else v


class RelatoEntrada(RelatoBase):
    """Payload enviado para análise da IA (pode conter foto)."""

    imagem_base64: str | None = Field(default=None, max_length=MAX_IMAGEM_B64)
    imagem_mime: Literal["image/jpeg", "image/png", "image/webp"] | None = None

    @field_validator("imagem_mime")
    @classmethod
    def mime_exige_imagem(cls, v, info):
        if v and not info.data.get("imagem_base64"):
            raise ValueError("imagem_mime informado sem imagem")
        return v


class AnaliseIA(BaseModel):
    """Saída ESTRUTURADA exigida do LLM. Qualquer resposta fora deste formato é rejeitada."""

    categoria: Categoria
    criticidade: Criticidade
    titulo: str = Field(min_length=3, max_length=90, description="Título curto do problema")
    resumo: str = Field(min_length=10, max_length=500, description="Resumo objetivo em linguagem simples")
    justificativa_criticidade: str = Field(max_length=400)
    orgao_responsavel: str = Field(max_length=150, description="Órgão/canal que costuma tratar o caso")
    orientacao_cidadao: str = Field(max_length=600, description="O que o cidadão pode fazer enquanto aguarda")
    risco_imediato: bool = Field(description="Há risco à vida ou à integridade física agora?")
    confianca: float = Field(ge=0, le=1)
    informacoes_faltantes: list[str] = Field(default_factory=list, max_length=5)


class AnaliseResposta(BaseModel):
    analise: AnaliseIA
    descricao_imagem: str | None = None
    modelo: str


class RelatoConfirmacao(RelatoBase):
    """Human-in-the-loop: o cidadão confirma ou corrige a análise antes de gerar o protocolo."""

    analise_ia: AnaliseIA
    categoria_final: Categoria
    criticidade_final: Criticidade
    tem_foto: bool = False
    tem_audio: bool = False


class EventoStatus(BaseModel):
    status: Status
    data: datetime
    observacao: str | None = None


class Protocolo(BaseModel):
    numero: str
    criado_em: datetime
    atualizado_em: datetime
    status: Status
    categoria: Categoria
    criticidade: Criticidade
    titulo: str
    resumo: str
    descricao: str
    endereco: str
    bairro: str
    cidade: str
    orgao_responsavel: str
    orientacao_cidadao: str
    risco_imediato: bool
    tem_foto: bool
    tem_audio: bool
    categoria_sugerida_ia: Categoria
    criticidade_sugerida_ia: Criticidade
    corrigido_pelo_cidadao: bool
    avaliacao: Literal["util", "incorreta"] | None = None
    comentario_avaliacao: str | None = None
    historico: list[EventoStatus] = Field(default_factory=list)
    demo: bool = False


class ProtocoloPublico(BaseModel):
    """Visão anonimizada para o painel público (sem descrição livre nem endereço)."""

    numero: str
    criado_em: datetime
    status: Status
    categoria: Categoria
    criticidade: Criticidade
    bairro: str
    cidade: str
    corrigido_pelo_cidadao: bool
    demo: bool = False


class AtualizacaoStatus(BaseModel):
    status: Status
    observacao: str | None = Field(default=None, max_length=300)


class Avaliacao(BaseModel):
    avaliacao: Literal["util", "incorreta"]
    comentario: str | None = Field(default=None, max_length=300)


class Transcricao(BaseModel):
    texto: str
