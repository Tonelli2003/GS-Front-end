"""Componentes visuais reutilizáveis (usados em várias telas com parâmetros diferentes)."""
import html
from datetime import datetime

import streamlit as st

from ui.rotulos import CRITICIDADES, categoria_txt, status_txt


def badge_criticidade(valor: str, tamanho: str = "normal") -> None:
    """Selo de criticidade: cor + ícone + texto (nunca só cor). Usado na análise, nos cards e no gestor."""
    icone, nome, cor = CRITICIDADES.get(valor, ("⚪", valor, "#444444"))
    fonte = "1.05rem" if tamanho == "grande" else "0.85rem"
    st.markdown(
        f'<span class="bed-badge" role="status" aria-label="Criticidade {nome}" '
        f'style="background:{cor};font-size:{fonte}">{icone} Criticidade: {nome}</span>',
        unsafe_allow_html=True,
    )


def estado_vazio(icone: str, titulo: str, dica: str) -> None:
    """Mensagem de estado vazio (usada em protocolos, painel, gestor e chat)."""
    st.markdown(
        f'<div class="bed-vazio"><div class="bed-vazio-icone" aria-hidden="true">{icone}</div>'
        f"<strong>{html.escape(titulo)}</strong><br><span>{html.escape(dica)}</span></div>",
        unsafe_allow_html=True,
    )


def _data(valor: str) -> str:
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except (ValueError, AttributeError):
        return str(valor)


def card_protocolo(p: dict, *, mostrar_endereco: bool = True, mostrar_historico: bool = False) -> None:
    """Cartão de protocolo. Morador vê com histórico; gestor vê com endereço completo."""
    with st.container(border=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"**{html.escape(p.get('titulo', 'Relato'))}**")
            st.caption(f"Protocolo **{p['numero']}** · aberto em {_data(p['criado_em'])}")
        with c2:
            badge_criticidade(p["criticidade"])
        st.markdown(f"{categoria_txt(p['categoria'])} &nbsp;·&nbsp; **Situação:** {status_txt(p['status'])}")
        if mostrar_endereco and p.get("endereco"):
            st.caption(f"📍 {p['endereco']} — {p['bairro']}, {p['cidade']}")
        if p.get("orgao_responsavel"):
            st.caption(f"🏛️ Responsável: {p['orgao_responsavel']}")
        if p.get("corrigido_pelo_cidadao"):
            st.caption("✏️ Classificação ajustada pelo morador antes do envio.")
        if mostrar_historico and p.get("historico"):
            with st.expander("Ver andamento"):
                for ev in p["historico"]:
                    obs = f" — {ev['observacao']}" if ev.get("observacao") else ""
                    st.markdown(f"- {_data(ev['data'])}: {status_txt(ev['status'])}{obs}")


def kpis(itens: list[tuple[str, str | int, str | None]]) -> None:
    """Linha de indicadores (rótulo, valor, ajuda)."""
    colunas = st.columns(len(itens))
    for col, (rotulo, valor, ajuda) in zip(colunas, itens):
        col.metric(rotulo, valor, help=ajuda)


def mostrar_erro(erro, acao: str = "") -> None:
    """Erro amigável padronizado, sem detalhes técnicos."""
    st.error(f"**Não deu certo{(' ' + acao) if acao else ''}.** {erro.mensagem}", icon="⚠️")
