"""Bairro em Dia — front-end Streamlit.

Rodar: streamlit run app.py  (dentro da pasta frontend/, com a API no ar)
"""
import streamlit as st

st.set_page_config(page_title="Bairro em Dia", page_icon="🏘️", layout="wide",
                   menu_items={"About": "Bairro em Dia — GS 2026/2 Front-end em Sistemas de IA (FIAP)"})

from features import assistente, gestor, meus_protocolos, novo_relato, painel, sidebar  # noqa: E402
from state.session import eh_gestor, init_state  # noqa: E402
from ui.acessibilidade import aplicar_tema  # noqa: E402

init_state()
sidebar.render()
aplicar_tema()

st.markdown(
    '<div class="bed-hero"><h1>🏘️ Bairro em Dia</h1>'
    "<p>Viu um buraco, poste apagado, lixo acumulado ou barulho fora de hora? Conte para a gente: "
    "a IA organiza seu relato, você confere e recebe um protocolo para acompanhar.</p></div>",
    unsafe_allow_html=True,
)

nomes = ["📝 Relatar problema", "📋 Meus protocolos", "💬 Assistente", "📊 Painel do bairro"]
if eh_gestor():
    nomes.append("🛠️ Gestão")
abas = st.tabs(nomes)

with abas[0]:
    novo_relato.render()
with abas[1]:
    meus_protocolos.render()
with abas[2]:
    assistente.render()
with abas[3]:
    painel.render()
if eh_gestor():
    with abas[4]:
        gestor.render()
