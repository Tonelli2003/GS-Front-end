"""Recursos de acessibilidade: tema de alto contraste, fonte maior e leitura em voz alta."""
import json

import streamlit as st

CSS_BASE = """
<style>
.bed-badge{display:inline-block;color:#fff;padding:.25rem .65rem;border-radius:999px;font-weight:700;}
.bed-vazio{text-align:center;padding:2rem 1rem;border:2px dashed rgba(128,128,128,.45);border-radius:12px;margin:.5rem 0;}
.bed-vazio-icone{font-size:2.4rem;}
.bed-hero{padding:.4rem 0 .2rem 0;}
.bed-hero h1{margin-bottom:0;}
:focus-visible{outline:3px solid #1A73E8 !important;outline-offset:2px;}
</style>
"""

CSS_ALTO_CONTRASTE = """
<style>
.stApp, [data-testid="stSidebar"], [data-testid="stHeader"]{background:#000 !important;}
.stApp *, [data-testid="stSidebar"] *{color:#fff !important;}
.bed-badge{border:2px solid #fff;}
a{color:#FFEB3B !important;text-decoration:underline !important;}
input, textarea, [data-baseweb="select"] *{background:#000 !important;border-color:#FFEB3B !important;}
button{border:2px solid #FFEB3B !important;}
</style>
"""

CSS_FONTE_GRANDE = """
<style>
html, .stApp, .stMarkdown p, label, input, textarea, button{font-size:1.18rem !important;}
</style>
"""


def aplicar_tema() -> None:
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    if st.session_state.get("alto_contraste"):
        st.markdown(CSS_ALTO_CONTRASTE, unsafe_allow_html=True)
    if st.session_state.get("fonte_grande"):
        st.markdown(CSS_FONTE_GRANDE, unsafe_allow_html=True)


def botao_ouvir(texto: str, rotulo: str = "🔊 Ouvir em voz alta") -> None:
    """Leitura em voz alta via Web Speech API do navegador (sem custo e sem enviar dados)."""
    # Escapa < > & para o texto (que pode vir do LLM) não conseguir fechar a tag <script>.
    seguro = json.dumps(texto).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    st.iframe(
        f"""
        <button id="b" aria-label="{rotulo}" style="cursor:pointer;padding:.35rem .8rem;border-radius:8px;
        border:1px solid #888;background:transparent;font-size:.9rem;color:inherit">{rotulo}</button>
        <script>
        const b=document.getElementById('b');
        b.style.color = window.parent.getComputedStyle(window.parent.document.body).color;
        b.onclick=()=>{{const s=window.speechSynthesis; s.cancel();
          const u=new SpeechSynthesisUtterance({seguro}); u.lang='pt-BR'; u.rate=0.95; s.speak(u);}};
        </script>""",
        height=45,
    )
