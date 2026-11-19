"""Tela 'Meus protocolos': histórico do morador guardado no estado da sessão."""
import pandas as pd
import streamlit as st

from providers import api_client as api
from providers.api_client import ErroAPI
from state import session
from ui.componentes import card_protocolo, estado_vazio, mostrar_erro
from ui.graficos import barras_por_categoria, preparar


def _consultar() -> None:
    with st.form("form_consulta", border=False):
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        numero = c1.text_input("Consultar um protocolo pelo número", placeholder="BED-2026-000123",
                               max_chars=20)
        ok = c2.form_submit_button("🔎 Consultar", width="stretch")
    if ok:
        if not numero.strip():
            st.warning("Digite o número do protocolo.", icon="✏️")
            return
        try:
            session.registrar_protocolo(api.consultar_protocolo(numero))
            st.session_state.ultimo_protocolo = None
            st.toast("Protocolo adicionado à sua lista.", icon="📋")
        except ErroAPI as e:
            mostrar_erro(e, "na consulta")


def _atualizar_todos() -> None:
    falhas = 0
    for numero in list(st.session_state.meus_protocolos):
        try:
            st.session_state.meus_protocolos[numero] = api.consultar_protocolo(numero)
        except ErroAPI:
            falhas += 1
    if falhas:
        st.warning(f"Não conseguimos atualizar {falhas} protocolo(s). Tente de novo mais tarde.", icon="⚠️")
    else:
        st.toast("Situação atualizada!", icon="🔄")


def _avaliacao(p: dict) -> None:
    if p.get("avaliacao"):
        txt = "👍 Você marcou a classificação como correta." if p["avaliacao"] == "util" else \
              "👎 Você marcou a classificação como incorreta. Obrigado por ajudar a melhorar a IA!"
        st.caption(txt)
        return
    st.caption("A classificação automática ajudou?")
    c1, c2, _ = st.columns([1, 1, 2])
    for col, valor, rotulo in ((c1, "util", "👍 Sim"), (c2, "incorreta", "👎 Não")):
        if col.button(rotulo, key=f"av_{valor}_{p['numero']}", width="stretch"):
            try:
                session.registrar_protocolo(api.avaliar_protocolo(p["numero"], valor))
                st.session_state.ultimo_protocolo = None
                st.rerun()
            except ErroAPI as e:
                mostrar_erro(e, "ao registrar sua avaliação")


def render() -> None:
    st.subheader("📋 Meus protocolos")
    _consultar()
    meus = session.lista_meus_protocolos()
    if not meus:
        estado_vazio("📭", "Você ainda não tem protocolos nesta sessão.",
                     "Registre um problema ou consulte um número que você já tem.")
        return

    c1, c2 = st.columns([3, 1], vertical_alignment="center")
    c1.markdown(f"Você acompanha **{len(meus)}** protocolo(s).")
    if c2.button("🔄 Atualizar situação", width="stretch"):
        _atualizar_todos()
        meus = session.lista_meus_protocolos()

    if len(meus) >= 2:
        df = preparar(pd.DataFrame(meus))
        st.plotly_chart(barras_por_categoria(df, titulo="Meus relatos por tipo", altura=260),
                        width="stretch")

    for p in meus:
        card_protocolo(p, mostrar_historico=True)
        _avaliacao(p)
