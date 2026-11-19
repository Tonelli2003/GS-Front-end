"""Painel público do bairro: indicadores e gráficos Plotly com filtros interativos."""
import pandas as pd
import streamlit as st

from providers import api_client as api
from providers.api_client import ErroAPI
from ui.componentes import estado_vazio, kpis, mostrar_erro
from ui.graficos import barras_por_categoria, linha_do_tempo, preparar, rosca_status
from ui.rotulos import CATEGORIAS, CRITICIDADES, STATUS, categoria_txt, criticidade_txt, status_txt


@st.cache_data(ttl=30, show_spinner=False)
def carregar_publico() -> list[dict]:
    return api.listar_publico()


def aplicar_filtros(df: pd.DataFrame, chave: str) -> pd.DataFrame:
    """Controles de filtro reutilizados no painel público e no painel do gestor."""
    c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.2, 1])
    inicio, fim = df["dia"].min(), df["dia"].max()
    periodo = c1.date_input("Período", value=(inicio, fim), min_value=inicio, max_value=fim,
                            format="DD/MM/YYYY", key=f"{chave}_periodo")
    cats = c2.multiselect("Tipo de problema", list(CATEGORIAS), format_func=categoria_txt,
                          placeholder="Todos", key=f"{chave}_cat")
    crits = c3.multiselect("Urgência", list(CRITICIDADES), format_func=criticidade_txt,
                           placeholder="Todas", key=f"{chave}_crit")
    bairros = ["Todos"] + sorted(df["bairro"].unique())
    bairro = c4.selectbox("Bairro", bairros, key=f"{chave}_bairro")
    status = st.pills("Situação", list(STATUS), format_func=status_txt, selection_mode="multi",
                      key=f"{chave}_status")

    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df = df[(df["dia"] >= periodo[0]) & (df["dia"] <= periodo[1])]
    if cats:
        df = df[df["categoria"].isin(cats)]
    if crits:
        df = df[df["criticidade"].isin(crits)]
    if bairro != "Todos":
        df = df[df["bairro"] == bairro]
    if status:
        df = df[df["status"].isin(status)]
    return df


def render() -> None:
    st.subheader("📊 Painel do bairro")
    st.caption("Dados anonimizados: aqui não aparecem endereços nem textos dos moradores.")
    try:
        dados = carregar_publico()
    except ErroAPI as e:
        mostrar_erro(e, "ao carregar o painel")
        if st.button("Tentar novamente", key="painel_retry"):
            carregar_publico.clear()
            st.rerun()
        return
    if not dados:
        estado_vazio("🗺️", "Ainda não há relatos registrados.", "Seja o primeiro: use a aba 'Relatar problema'.")
        return

    df = preparar(pd.DataFrame(dados))
    filtrado = aplicar_filtros(df, "pub")
    if filtrado.empty:
        estado_vazio("🔍", "Nenhum relato com esses filtros.", "Tente ampliar o período ou limpar os filtros.")
        return

    abertos = filtrado[~filtrado["status"].isin(["resolvido", "recusado"])]
    graves = abertos[abertos["criticidade"].isin(["alta", "urgente"])]
    resolvidos = (filtrado["status"] == "resolvido").mean() * 100
    concordancia = (1 - filtrado["corrigido_pelo_cidadao"].mean()) * 100
    kpis([
        ("Relatos", len(filtrado), "Total no filtro atual"),
        ("🟠🔴 Graves em aberto", len(graves), "Urgência alta ou urgente ainda sem solução"),
        ("✅ Resolvidos", f"{resolvidos:.0f}%", "Percentual com situação 'Resolvido'"),
        ("🤝 IA confirmada", f"{concordancia:.0f}%", "Relatos em que o morador não precisou corrigir a IA"),
    ])

    st.plotly_chart(barras_por_categoria(filtrado), width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(linha_do_tempo(filtrado), width="stretch")
    with c2:
        st.plotly_chart(rosca_status(filtrado), width="stretch")
    if bool(df.get("demo", pd.Series(dtype=bool)).any()):
        st.caption("ℹ️ Inclui dados fictícios de demonstração.")
