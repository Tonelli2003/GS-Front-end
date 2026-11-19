"""Cliente HTTP da API Bairro em Dia. Única camada do front que conversa com o back-end.

Converte qualquer falha técnica em ErroAPI com mensagem amigável para o cidadão.
"""
import base64
import os

import httpx
import streamlit as st


def _api_url() -> str:
    try:
        url = st.secrets.get("API_URL")  # Streamlit Cloud
    except Exception:  # noqa: BLE001 - sem secrets.toml localmente
        url = None
    return (url or os.getenv("API_URL", "http://localhost:8000")).rstrip("/")


class ErroAPI(Exception):
    def __init__(self, mensagem: str, codigo: str = "ERRO", campos: list[str] | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo
        self.campos = campos or []


MENSAGENS = {
    "API_FORA": "Não conseguimos falar com o serviço agora. Verifique sua internet e tente de novo em instantes.",
    "TIMEOUT": "O serviço demorou para responder. Tente novamente — seus dados não foram perdidos.",
    "RESPOSTA_INVALIDA": "Recebemos uma resposta inesperada do serviço. Tente novamente.",
}


@st.cache_resource
def _cliente() -> httpx.Client:
    """Conexão HTTP reaproveitada entre reruns (cache_resource)."""
    return httpx.Client(base_url=_api_url(), timeout=httpx.Timeout(45.0, connect=5.0))


def _req(metodo: str, caminho: str, *, campos_obrigatorios: tuple[str, ...] = (), **kwargs):
    try:
        r = _cliente().request(metodo, caminho, **kwargs)
    except httpx.TimeoutException:
        raise ErroAPI(MENSAGENS["TIMEOUT"], "TIMEOUT")
    except httpx.HTTPError:
        raise ErroAPI(MENSAGENS["API_FORA"], "API_FORA")

    if r.status_code == 204:
        return None
    try:
        corpo = r.json()
    except ValueError:
        raise ErroAPI(MENSAGENS["RESPOSTA_INVALIDA"], "RESPOSTA_INVALIDA")

    if r.status_code >= 400:
        if isinstance(corpo, dict) and "mensagem" in corpo:
            raise ErroAPI(corpo["mensagem"], corpo.get("codigo", "ERRO"), corpo.get("campos"))
        raise ErroAPI("Não foi possível concluir agora. Tente novamente.", f"HTTP_{r.status_code}")

    if campos_obrigatorios and (
        not isinstance(corpo, dict) or any(c not in corpo for c in campos_obrigatorios)
    ):
        raise ErroAPI(MENSAGENS["RESPOSTA_INVALIDA"], "RESPOSTA_INVALIDA")
    return corpo


# ------------------------------------------------------------------ endpoints
def saude() -> dict:
    return _req("GET", "/health", campos_obrigatorios=("status",))


def buscar_cep(cep: str) -> dict:
    return _req("GET", f"/localizacao/cep/{cep}", campos_obrigatorios=("bairro", "cidade"))


def transcrever_audio(conteudo: bytes, nome: str, mime: str) -> str:
    corpo = _req("POST", "/relatos/transcrever", files={"arquivo": (nome, conteudo, mime)},
                 campos_obrigatorios=("texto",))
    return corpo["texto"]


def analisar_relato(payload: dict) -> dict:
    corpo = _req("POST", "/relatos/analisar", json=payload, campos_obrigatorios=("analise",))
    if not isinstance(corpo["analise"], dict) or "categoria" not in corpo["analise"]:
        raise ErroAPI(MENSAGENS["RESPOSTA_INVALIDA"], "RESPOSTA_INVALIDA")
    return corpo


def criar_protocolo(payload: dict) -> dict:
    return _req("POST", "/relatos", json=payload, campos_obrigatorios=("numero", "status"))


def consultar_protocolo(numero: str) -> dict:
    return _req("GET", f"/relatos/{numero.strip().upper()}", campos_obrigatorios=("numero",))


def avaliar_protocolo(numero: str, avaliacao: str, comentario: str | None = None) -> dict:
    return _req("POST", f"/relatos/{numero}/avaliacao",
                json={"avaliacao": avaliacao, "comentario": comentario or None})


def listar_publico() -> list[dict]:
    corpo = _req("GET", "/relatos/publico")
    if not isinstance(corpo, list):
        raise ErroAPI(MENSAGENS["RESPOSTA_INVALIDA"], "RESPOSTA_INVALIDA")
    return corpo


def perguntar_assistente(pergunta: str, historico: list[dict], cidade: str | None) -> dict:
    return _req("POST", "/assistente/perguntar",
                json={"pergunta": pergunta, "historico": historico, "cidade": cidade},
                campos_obrigatorios=("resposta",))


def feedback_assistente(pergunta: str, util: bool) -> None:
    _req("POST", "/assistente/feedback", json={"pergunta": pergunta[:800], "util": util})


# ----- gestor
def validar_gestor(token: str) -> bool:
    try:
        _req("POST", "/auth/gestor", headers={"X-Gestor-Token": token})
        return True
    except ErroAPI as e:
        if e.codigo == "NAO_AUTORIZADO":
            return False
        raise


def listar_gestor(token: str) -> list[dict]:
    return _req("GET", "/relatos", headers={"X-Gestor-Token": token})


def atualizar_status(token: str, numero: str, status: str, observacao: str | None) -> dict:
    return _req("PATCH", f"/relatos/{numero}/status", headers={"X-Gestor-Token": token},
                json={"status": status, "observacao": observacao or None})


def arquivo_para_base64(conteudo: bytes) -> str:
    return base64.b64encode(conteudo).decode("ascii")
