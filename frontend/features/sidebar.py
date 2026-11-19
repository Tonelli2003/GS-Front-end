"""Barra lateral: status do serviço, perfil (morador/gestor) e acessibilidade."""
import streamlit as st

from providers import api_client as api
from providers.api_client import ErroAPI


@st.cache_data(ttl=15, show_spinner=False)
def _saude() -> dict | None:
    try:
        return api.saude()
    except ErroAPI:
        return None


def _login_gestor() -> None:
    if st.session_state.gestor_token:
        st.success("Acesso de gestor ativo.", icon="🔐")
        if st.button("Sair do modo gestor"):
            st.session_state.gestor_token = None
            st.session_state.perfil = "Morador"
            st.rerun()
        return
    with st.form("login_gestor", border=False):
        token = st.text_input("Código de acesso do gestor", type="password")
        if st.form_submit_button("Entrar"):
            try:
                if api.validar_gestor(token):
                    st.session_state.gestor_token = token
                    st.rerun()
                else:
                    st.error("Código inválido.", icon="⛔")
            except ErroAPI as e:
                st.error(e.mensagem, icon="⚠️")


def render() -> None:
    with st.sidebar:
        st.markdown("## 🏘️ Bairro em Dia")
        st.caption("Seu bairro cuidado, um relato de cada vez.")

        saude = _saude()
        if saude is None:
            st.error("Serviço indisponível no momento. Você pode navegar, mas o envio pode falhar.", icon="🔌")
        elif not saude.get("ia_configurada"):
            st.warning("Serviço no ar, mas a análise por IA está desativada.", icon="🧠")
        else:
            st.success("Serviço online", icon="🟢")

        st.divider()
        st.radio("Você é:", ["Morador", "Gestor"], key="perfil", horizontal=True)
        if st.session_state.perfil == "Gestor":
            _login_gestor()

        st.divider()
        st.markdown("**Acessibilidade**")
        st.toggle("Alto contraste", key="alto_contraste")
        st.toggle("Letras maiores", key="fonte_grande")

        st.divider()
        with st.expander("🔒 Privacidade"):
            st.caption("Não pedimos nome, CPF ou telefone. O painel público mostra só dados agregados, "
                       "sem endereço ou texto. Evite fotos com rostos ou placas. A IA pode errar: "
                       "por isso você confere tudo antes de enviar.")
