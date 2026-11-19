"""Estado centralizado da sessão (st.session_state). Nenhuma feature cria chaves soltas fora daqui."""
from datetime import datetime

import streamlit as st

PADROES = {
    # preferências / perfil
    "perfil": "Morador",
    "gestor_token": None,
    "alto_contraste": False,
    "fonte_grande": False,
    "cidade_padrao": "São Paulo",
    # fluxo de novo relato
    "f_endereco": "",
    "f_bairro": "",
    "f_cidade": "São Paulo",
    "f_cep": "",
    "f_descricao": "",
    "f_transcricao": "",
    "rascunho": None,          # payload enviado para análise (sem a imagem)
    "analise_atual": None,     # resposta estruturada da IA aguardando confirmação
    "ultimo_protocolo": None,
    "cep_msg": None,           # (tipo, texto) da última busca de CEP
    # histórico do cidadão (alimenta lista e gráfico de "Meus protocolos")
    "meus_protocolos": {},     # numero -> protocolo (dict)
    # assistente
    "chat": [],                # [{papel, texto, estruturada?}]
    "chat_feedback": {},       # índice -> bool
}


def init_state() -> None:
    for chave, valor in PADROES.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor.copy() if isinstance(valor, (dict, list)) else valor


def eh_gestor() -> bool:
    return st.session_state.perfil == "Gestor" and bool(st.session_state.gestor_token)


# ----------------- relato
def guardar_analise(rascunho: dict, analise: dict) -> None:
    st.session_state.rascunho = rascunho
    st.session_state.analise_atual = analise


def limpar_relato() -> None:
    for chave in ("f_endereco", "f_bairro", "f_cep", "f_descricao", "f_transcricao"):
        st.session_state[chave] = ""
    st.session_state.rascunho = None
    st.session_state.analise_atual = None


def registrar_protocolo(protocolo: dict) -> None:
    st.session_state.meus_protocolos[protocolo["numero"]] = protocolo
    st.session_state.ultimo_protocolo = protocolo["numero"]


def lista_meus_protocolos() -> list[dict]:
    return sorted(st.session_state.meus_protocolos.values(), key=lambda p: p["criado_em"], reverse=True)


# ----------------- chat
def adicionar_mensagem(papel: str, texto: str, estruturada: dict | None = None) -> None:
    st.session_state.chat.append(
        {"papel": papel, "texto": texto, "estruturada": estruturada, "hora": datetime.now().strftime("%H:%M")}
    )


def historico_para_api(limite: int = 6) -> list[dict]:
    return [{"papel": m["papel"], "texto": m["texto"][:2000]} for m in st.session_state.chat[-limite:]]
