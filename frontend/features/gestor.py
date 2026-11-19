"""Visão do gestor (RBAC): fila de protocolos e atualização de andamento."""
import pandas as pd
import streamlit as st

from features.painel import aplicar_filtros, carregar_publico
from providers import api_client as api
from providers.api_client import ErroAPI
from ui.componentes import card_protocolo, estado_vazio, kpis, mostrar_erro
from ui.graficos import preparar
from ui.rotulos import ORDEM_CRITICIDADE, STATUS, status_txt


@st.cache_data(ttl=20, show_spinner=False)
def carregar_fila(token: str) -> list[dict]:
    return api.listar_gestor(token)


def _form_status(p: dict, token: str) -> None:
    with st.form(f"st_{p['numero']}", border=False):
        c1, c2, c3 = st.columns([1.2, 2, 1], vertical_alignment="bottom")
        opcoes = list(STATUS)
        novo = c1.selectbox("Nova situação", opcoes, index=opcoes.index(p["status"]), format_func=status_txt)
        obs = c2.text_input("Observação para o morador", max_chars=300,
                            placeholder="Ex.: Equipe agendada para sexta-feira")
        if c3.form_submit_button("Salvar", width="stretch"):
            try:
                api.atualizar_status(token, p["numero"], novo, obs)
            except ErroAPI as e:
                mostrar_erro(e, "ao atualizar")
                return
            carregar_fila.clear()
            carregar_publico.clear()
            st.toast(f"{p['numero']} atualizado para {status_txt(novo)}", icon="✅")
            st.rerun()


def render() -> None:
    st.subheader("🛠️ Gestão de protocolos")
    token = st.session_state.gestor_token
    try:
        fila = carregar_fila(token)
    except ErroAPI as e:
        mostrar_erro(e, "ao carregar a fila")
        return
    if not fila:
        estado_vazio("✅", "Nenhum protocolo na fila.", "Quando moradores enviarem relatos, eles aparecem aqui.")
        return

    df = preparar(pd.DataFrame(fila))
    filtrado = aplicar_filtros(df, "gest")
    kpis([
        ("Na fila (filtro)", len(filtrado), None),
        ("🔴 Urgentes", int((filtrado["criticidade"] == "urgente").sum()), None),
        ("✏️ Corrigidos pelo morador", int(filtrado["corrigido_pelo_cidadao"].sum()),
         "Casos em que a IA errou e o morador ajustou: bons exemplos para melhorar o prompt"),
        ("👎 Avaliados como incorretos", int((filtrado["avaliacao"] == "incorreta").sum()), None),
    ])
    if filtrado.empty:
        estado_vazio("🔍", "Nada com esses filtros.", "Ajuste os filtros acima.")
        return

    filtrado = filtrado.assign(_ord=filtrado["criticidade"].map({c: i for i, c in enumerate(reversed(ORDEM_CRITICIDADE))}))
    filtrado = filtrado.sort_values(["_ord", "criado_em"], ascending=[True, True])
    por_numero = {p["numero"]: p for p in fila}
    st.caption(f"Mostrando {min(len(filtrado), 30)} de {len(filtrado)} — ordenados por urgência e antiguidade.")
    for numero in filtrado["numero"].head(30):
        p = por_numero[numero]
        card_protocolo(p, mostrar_endereco=True, mostrar_historico=True)
        with st.expander(f"Relato completo e ações — {numero}"):
            st.markdown(f"> {p['descricao']}")
            if p.get("corrigido_pelo_cidadao"):
                st.caption(f"IA sugeriu: {p['categoria_sugerida_ia']} / {p['criticidade_sugerida_ia']}")
            _form_status(p, token)
