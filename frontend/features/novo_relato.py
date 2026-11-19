"""Tela 'Relatar problema': entrada validada -> análise da IA -> confirmação humana -> protocolo."""
import json
import re

import streamlit as st

from features.painel import carregar_publico
from providers import api_client as api
from providers.api_client import ErroAPI
from state import session
from ui.acessibilidade import botao_ouvir
from ui.componentes import badge_criticidade, mostrar_erro
from ui.rotulos import CATEGORIAS, CRITICIDADES, categoria_txt, criticidade_txt

FOTO_MAX = 4 * 1024 * 1024
AUDIO_MAX = 10 * 1024 * 1024
RE_CEP = re.compile(r"^\d{5}-?\d{3}$")


@st.cache_data(show_spinner=False, ttl=900, max_entries=30)
def _analisar_cache(payload_json: str) -> dict:
    """Mesmo relato enviado de novo (ex.: rerun, clique duplo) não gera nova chamada ao LLM."""
    return api.analisar_relato(json.loads(payload_json))


# ------------------------------------------------------------------ callbacks
def _cb_buscar_cep() -> None:
    cep = st.session_state.f_cep.strip()
    if not RE_CEP.match(cep):
        st.session_state.cep_msg = ("erro", "CEP deve ter 8 números, ex.: 01310-100.")
        return
    try:
        d = api.buscar_cep(cep)
    except ErroAPI as e:
        st.session_state.cep_msg = ("erro", e.mensagem)
        return
    st.session_state.f_bairro = d["bairro"] or st.session_state.f_bairro
    st.session_state.f_cidade = d["cidade"] or st.session_state.f_cidade
    if d.get("logradouro") and not st.session_state.f_endereco:
        st.session_state.f_endereco = f"{d['logradouro']}, "
    st.session_state.cep_msg = ("ok", f"Encontrado: {d.get('logradouro') or 'logradouro não informado'} — "
                                      f"{d['bairro']}, {d['cidade']}/{d['uf']}. Complete o número.")


def _cb_transcrever() -> None:
    audio = st.session_state.get("audio_gravado") or st.session_state.get("audio_arquivo")
    if audio is None:
        st.session_state.cep_msg = None
        st.session_state["audio_msg"] = ("erro", "Grave ou anexe um áudio antes de transcrever.")
        return
    conteudo = audio.getvalue()
    if len(conteudo) > AUDIO_MAX:
        st.session_state["audio_msg"] = ("erro", "O áudio deve ter no máximo 10 MB.")
        return
    try:
        texto = api.transcrever_audio(conteudo, audio.name or "audio.wav", audio.type or "audio/wav")
    except ErroAPI as e:
        st.session_state["audio_msg"] = ("erro", e.mensagem)
        return
    st.session_state.f_transcricao = texto
    st.session_state["audio_msg"] = ("ok", "Áudio transcrito! Confira o texto abaixo e corrija se precisar.")


def _mensagem(chave: str) -> None:
    msg = st.session_state.get(chave)
    if msg:
        (st.success if msg[0] == "ok" else st.warning)(msg[1], icon="✅" if msg[0] == "ok" else "⚠️")


# ------------------------------------------------------------------ validação
def validar(d: dict, foto) -> list[str]:
    erros = []
    if len(d["endereco"]) < 5:
        erros.append("Informe a rua e o número, ou um ponto de referência (mínimo 5 letras).")
    if len(d["bairro"]) < 2:
        erros.append("Informe o bairro.")
    if len(d["cidade"]) < 2:
        erros.append("Informe a cidade.")
    if len(d["descricao"]) < 20:
        erros.append("Descreva o problema com pelo menos 20 caracteres (ou grave um áudio e transcreva).")
    if len(d["descricao"]) > 1500:
        erros.append("A descrição pode ter no máximo 1500 caracteres.")
    if d.get("cep") and not RE_CEP.match(d["cep"]):
        erros.append("CEP inválido. Use 8 números, ex.: 01310-100.")
    if foto is not None and foto.size > FOTO_MAX:
        erros.append("A foto deve ter no máximo 4 MB.")
    return erros


# ------------------------------------------------------------------ etapas
def _etapa_formulario() -> None:
    st.markdown("#### 1. Onde é o problema?")
    c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
    c1.text_input("CEP (opcional — preenche bairro e cidade)", key="f_cep", max_chars=9, placeholder="00000-000")
    c2.button("🔎 Buscar CEP", on_click=_cb_buscar_cep, width="stretch")
    _mensagem("cep_msg")

    with st.expander("🎙️ Prefere falar? Grave ou anexe um áudio (opcional)"):
        st.audio_input("Gravar áudio descrevendo o problema", key="audio_gravado")
        st.file_uploader("…ou anexe um arquivo de áudio", type=["wav", "mp3", "m4a", "ogg", "webm"],
                         key="audio_arquivo", help="Até 10 MB.")
        st.button("📝 Transcrever áudio", on_click=_cb_transcrever)
        _mensagem("audio_msg")

    with st.form("form_relato", border=True):
        st.text_input("Endereço ou ponto de referência *", key="f_endereco", max_chars=200,
                      placeholder="Ex.: Rua das Flores, 120 — em frente à padaria")
        c1, c2 = st.columns(2)
        c1.text_input("Bairro *", key="f_bairro", max_chars=80)
        c2.text_input("Cidade *", key="f_cidade", max_chars=80)
        st.markdown("#### 2. O que está acontecendo?")
        st.text_area("Descreva o problema *", key="f_descricao", max_chars=1500, height=130,
                     placeholder="Ex.: Tem um buraco grande na pista há 2 semanas, motos estão desviando "
                                 "para a contramão. Fica pior quando chove.",
                     help="Conte o que é, há quanto tempo acontece e se há risco para alguém.")
        if st.session_state.f_transcricao:
            st.text_area("Texto do áudio (você pode corrigir)", key="f_transcricao", max_chars=3000)
        foto = st.file_uploader("📷 Foto do problema (opcional)", type=["jpg", "jpeg", "png", "webp"],
                                help="Até 4 MB. Evite mostrar rostos ou placas de carro.")
        enviado = st.form_submit_button("🧠 Analisar meu relato", type="primary", width="stretch")
    st.caption("* Campos obrigatórios. Não pedimos nome, CPF ou telefone: você acompanha pelo número do protocolo.")

    if not enviado:
        return

    descricao = st.session_state.f_descricao.strip() or st.session_state.f_transcricao.strip()
    dados = {
        "descricao": descricao,
        "endereco": st.session_state.f_endereco.strip(),
        "bairro": st.session_state.f_bairro.strip(),
        "cidade": st.session_state.f_cidade.strip(),
        "cep": st.session_state.f_cep.strip() or None,
        "transcricao_audio": st.session_state.f_transcricao.strip() or None,
    }
    erros = validar(dados, foto)
    if erros:
        st.error("**Faltam alguns ajustes:**\n\n" + "\n".join(f"- {e}" for e in erros), icon="✏️")
        return

    payload = dict(dados)
    if foto is not None:
        mime = "image/jpeg" if foto.type in ("image/jpg", "image/jpeg") else foto.type
        payload |= {"imagem_base64": api.arquivo_para_base64(foto.getvalue()), "imagem_mime": mime}

    with st.status("Analisando seu relato…", expanded=True) as status:
        st.write("📤 Enviando com segurança para o serviço")
        if foto is not None:
            st.write("🖼️ Observando a foto")
        st.write("🧠 Identificando o tipo de problema e a urgência")
        try:
            resposta = _analisar_cache(json.dumps(payload, sort_keys=True, ensure_ascii=False))
        except ErroAPI as e:
            status.update(label="Não foi possível analisar agora", state="error")
            mostrar_erro(e, "na análise")
            st.caption("Seu texto continua preenchido acima — é só tentar de novo.")
            return
        status.update(label="Análise pronta!", state="complete", expanded=False)

    rascunho = dados | {"tem_foto": foto is not None, "tem_audio": bool(dados["transcricao_audio"])}
    session.guardar_analise(rascunho, resposta)
    st.rerun()


def _etapa_confirmacao() -> None:
    resp = st.session_state.analise_atual
    a = resp["analise"]
    rascunho = st.session_state.rascunho

    st.markdown("#### 3. Confira a análise antes de enviar")
    if a.get("risco_imediato"):
        st.error("**Pode haver risco imediato.** Se alguém estiver em perigo, ligue agora: "
                 "**193** Bombeiros · **192** SAMU · **190** Polícia · **199** Defesa Civil.", icon="🚨")

    with st.container(border=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"### {a['titulo']}")
            st.markdown(f"**Tipo:** {categoria_txt(a['categoria'])}")
        with c2:
            badge_criticidade(a["criticidade"], "grande")
            st.caption(f"Confiança da IA: {round(a.get('confianca', 0) * 100)}%")
        st.markdown(f"**Resumo:** {a['resumo']}")
        st.markdown(f"**Por que essa urgência:** {a['justificativa_criticidade']}")
        st.markdown(f"**Quem costuma resolver:** {a['orgao_responsavel']}")
        st.info(f"**O que você pode fazer agora:** {a['orientacao_cidadao']}", icon="💡")
        if resp.get("descricao_imagem"):
            st.caption(f"🖼️ O que a IA entendeu da foto: {resp['descricao_imagem']}")
        if a.get("informacoes_faltantes"):
            st.warning("Para agilizar, vale incluir: " + "; ".join(a["informacoes_faltantes"]), icon="📝")
        botao_ouvir(f"{a['titulo']}. Urgência {CRITICIDADES[a['criticidade']][1]}. {a['resumo']} "
                    f"O que você pode fazer agora: {a['orientacao_cidadao']}")
        with st.expander("Ver o que você escreveu"):
            st.write(f"📍 {rascunho['endereco']} — {rascunho['bairro']}, {rascunho['cidade']}")
            st.write(rascunho["descricao"])

    st.markdown("**A classificação da IA está correta?**")
    escolha = st.radio("A classificação está correta?", ["✅ Sim, está correta", "✏️ Não, quero corrigir"],
                       horizontal=True, label_visibility="collapsed", key="hitl_escolha")
    cat_final, crit_final = a["categoria"], a["criticidade"]
    if escolha.startswith("✏️"):
        c1, c2 = st.columns(2)
        cats, crits = list(CATEGORIAS), list(CRITICIDADES)
        cat_final = c1.selectbox("Tipo de problema correto", cats, index=cats.index(a["categoria"]),
                                 format_func=categoria_txt)
        crit_final = c2.selectbox("Urgência correta", crits, index=crits.index(a["criticidade"]),
                                  format_func=criticidade_txt)

    b1, b2 = st.columns([2, 1])
    if b1.button("📨 Confirmar e gerar protocolo", type="primary", width="stretch"):
        payload = rascunho | {"analise_ia": a, "categoria_final": cat_final, "criticidade_final": crit_final}
        with st.spinner("Gerando seu protocolo…"):
            try:
                protocolo = api.criar_protocolo(payload)
            except ErroAPI as e:
                mostrar_erro(e, "ao gerar o protocolo")
                return
        session.registrar_protocolo(protocolo)
        session.limpar_relato()
        carregar_publico.clear()  # painel passa a refletir o novo relato
        st.rerun()
    if b2.button("🗑️ Descartar", width="stretch"):
        session.limpar_relato()
        st.rerun()


def render() -> None:
    st.subheader("📝 Relatar um problema no bairro")
    numero = st.session_state.ultimo_protocolo
    if numero:
        st.success(f"**Relato enviado! Seu protocolo é {numero}.** Anote este número: com ele você "
                   "acompanha o andamento na aba *Meus protocolos*.", icon="🎉")
        if st.button("Registrar outro problema"):
            st.session_state.ultimo_protocolo = None
            st.rerun()
        return
    if st.session_state.analise_atual:
        _etapa_confirmacao()
    else:
        _etapa_formulario()
