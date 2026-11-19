"""Tela 'Assistente': chat que orienta o cidadão sobre onde e como buscar atendimento."""
import streamlit as st

from providers import api_client as api
from providers.api_client import ErroAPI
from state import session
from ui.acessibilidade import botao_ouvir
from ui.componentes import estado_vazio

SUGESTOES = [
    "O poste da minha rua está apagado. O que eu faço?",
    "Tem um bar com som alto toda madrugada. Pra quem eu ligo?",
    "Uma árvore caiu em cima dos fios. É perigoso?",
    "Esgoto está vazando na calçada.",
]


def _cb_feedback(indice: int) -> None:
    valor = st.session_state.get(f"fb_{indice}")
    if valor is None:
        return
    st.session_state.chat_feedback[indice] = bool(valor)
    pergunta = st.session_state.chat[indice - 1]["texto"] if indice > 0 else ""
    try:
        api.feedback_assistente(pergunta, bool(valor))
    except ErroAPI:
        pass  # feedback é opcional; não incomodamos o cidadão


def _render_resposta(r: dict, indice: int) -> None:
    if r.get("emergencia"):
        st.error("**Situação de risco:** se alguém estiver em perigo, ligue agora — "
                 "193 Bombeiros · 192 SAMU · 190 Polícia · 199 Defesa Civil.", icon="🚨")
    st.markdown(r["resposta"])
    if r.get("passos"):
        st.markdown("**Passo a passo:**\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(r["passos"], 1)))
    if r.get("canais"):
        st.markdown("**Onde buscar atendimento:**")
        cols = st.columns(min(len(r["canais"]), 2))
        for i, c in enumerate(r["canais"]):
            with cols[i % len(cols)].container(border=True):
                st.markdown(f"**📞 {c['nome']}**")
                st.caption(f"**Como:** {c['como_acessar']}")
                st.caption(f"**Quando:** {c['quando_usar']}")
    if r.get("aviso"):
        st.caption(f"ℹ️ {r['aviso']}")
    botao_ouvir(r["resposta"] + " " + " ".join(r.get("passos", [])), rotulo="🔊 Ouvir resposta")
    st.feedback("thumbs", key=f"fb_{indice}", on_change=_cb_feedback, args=(indice,))


def _cb_pergunta_voz() -> None:
    """Ajuste pós-teste com usuários: quem não gosta de digitar pode perguntar falando."""
    audio = st.session_state.get("audio_pergunta")
    if audio is None:
        st.session_state["voz_msg"] = "Grave sua pergunta antes de enviar."
        return
    try:
        texto = api.transcrever_audio(audio.getvalue(), audio.name or "pergunta.wav", audio.type or "audio/wav")
    except ErroAPI as e:
        st.session_state["voz_msg"] = e.mensagem
        return
    st.session_state["voz_msg"] = None
    st.session_state["pergunta_pendente"] = texto


def _perguntar(texto: str) -> None:
    texto = texto.strip()
    if not 3 <= len(texto) <= 800:
        st.warning("Escreva uma pergunta entre 3 e 800 caracteres.", icon="✏️")
        return
    historico = session.historico_para_api()
    session.adicionar_mensagem("cidadao", texto)
    with st.spinner("O assistente está consultando os canais de atendimento…"):
        try:
            r = api.perguntar_assistente(texto, historico, st.session_state.f_cidade or None)
            session.adicionar_mensagem("assistente", r["resposta"], estruturada=r)
        except ErroAPI as e:
            session.adicionar_mensagem("assistente", f"⚠️ {e.mensagem}")
    st.rerun()


def render() -> None:
    st.subheader("💬 Assistente do cidadão")
    st.caption("Tire dúvidas sobre onde e como pedir atendimento. As respostas usam uma lista de canais "
               "oficiais revisada pela equipe. Em emergências, ligue 190, 192, 193 ou 199.")

    st.info("**Como usar:** 1️⃣ toque em uma das perguntas prontas, **ou** 2️⃣ grave sua pergunta por voz, "
            "**ou** 3️⃣ escreva na caixa lá embaixo e aperte Enter.", icon="👋")

    if not st.session_state.chat:
        estado_vazio("🤖", "Como posso ajudar?", "Escolha uma pergunta pronta, fale ou escreva a sua.")

    # Perguntas prontas ficam SEMPRE visíveis (ajuste após teste com usuários)
    st.markdown("**Perguntas prontas:**")
    cols = st.columns(2)
    for i, s in enumerate(SUGESTOES):
        if cols[i % 2].button(s, key=f"sug_{i}", width="stretch"):
            _perguntar(s)

    with st.expander("🎙️ Perguntar falando (sem digitar)"):
        st.audio_input("Toque no microfone, fale sua dúvida e toque de novo para parar", key="audio_pergunta")
        st.button("📨 Enviar pergunta falada", on_click=_cb_pergunta_voz)
        if st.session_state.get("voz_msg"):
            st.warning(st.session_state["voz_msg"], icon="⚠️")

    if st.session_state.chat and st.button("🧹 Nova conversa"):
        st.session_state.chat = []
        st.session_state.chat_feedback = {}
        st.rerun()

    for i, m in enumerate(st.session_state.chat):
        papel = "user" if m["papel"] == "cidadao" else "assistant"
        with st.chat_message(papel, avatar="🙂" if papel == "user" else "🏘️"):
            if m.get("estruturada"):
                _render_resposta(m["estruturada"], i)
            else:
                st.markdown(m["texto"])

    pendente = st.session_state.pop("pergunta_pendente", None)
    if pendente:
        _perguntar(pendente)
    pergunta = st.chat_input("✍️ Escreva sua dúvida aqui e aperte Enter…", max_chars=800)
    if pergunta:
        _perguntar(pergunta)
