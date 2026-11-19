import json
from types import SimpleNamespace

import pytest

from app.pipelines.classificacao import analisar_relato, montar_mensagem
from app.providers.llm import GroqProvider, LLMError, LLMRespostaInvalida
from app.schemas.relato import AnaliseIA, RelatoEntrada
from tests.conftest import LLMFalso

ENTRADA = RelatoEntrada(
    descricao="Fio de energia caído no chão perto da escola, crianças passando.",
    endereco="Rua A, 10",
    bairro="Lapa",
)


def test_risco_imediato_forca_urgente():
    resp = analisar_relato(ENTRADA, LLMFalso(risco=True), "fake")
    assert resp.analise.criticidade.value == "urgente"


def test_imagem_entra_no_prompt():
    entrada = ENTRADA.model_copy(update={"imagem_base64": "aGVsbG8=", "imagem_mime": "image/jpeg"})
    llm = LLMFalso()
    resp = analisar_relato(entrada, llm, "fake")
    assert resp.descricao_imagem and "Descrição automática da foto" in llm.ultima_mensagem


def test_falha_na_visao_nao_derruba_analise():
    class SemVisao(LLMFalso):
        def descrever_imagem(self, *_):
            raise LLMError("visão fora")

    entrada = ENTRADA.model_copy(update={"imagem_base64": "aGVsbG8=", "imagem_mime": "image/jpeg"})
    resp = analisar_relato(entrada, SemVisao(), "fake")
    assert resp.descricao_imagem is None and resp.analise.categoria


def test_mensagem_isola_texto_do_cidadao():
    msg = montar_mensagem(ENTRADA, None)
    assert '"""' in msg and "Lapa" in msg


# ---- GroqProvider com cliente simulado: corrige JSON inválido na 2ª tentativa ----
VALIDO = {
    "categoria": "iluminacao", "criticidade": "alta", "titulo": "Rua escura",
    "resumo": "Postes apagados na rua inteira.", "justificativa_criticidade": "Risco à segurança.",
    "orgao_responsavel": "Prefeitura", "orientacao_cidadao": "Evite passar à noite.",
    "risco_imediato": False, "confianca": 0.8, "informacoes_faltantes": [],
}


def _provider_com_respostas(respostas):
    p = GroqProvider.__new__(GroqProvider)
    import groq

    p._groq = groq
    p.cfg = SimpleNamespace(groq_model="m")
    fila = list(respostas)
    criar = lambda **_: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=fila.pop(0)))])
    p.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=criar)))
    return p


def test_provider_reprocessa_json_invalido():
    p = _provider_com_respostas(['{"categoria": "xyz"}', json.dumps(VALIDO)])
    assert p.gerar_json("s", "u", AnaliseIA).categoria.value == "iluminacao"


def test_provider_desiste_apos_tres_falhas():
    p = _provider_com_respostas(["não é json", "{}", "[]"])
    with pytest.raises(LLMRespostaInvalida):
        p.gerar_json("s", "u", AnaliseIA)


def test_provider_recupera_de_json_rejeitado_pela_groq():
    """Caso 6 da avaliação: a Groq devolve 400 json_validate_failed; o provider deve tentar de novo."""
    import groq
    import httpx

    p = _provider_com_respostas([json.dumps(VALIDO)])
    chamadas = {"n": 0}
    original = p.client.chat.completions.create

    def criar(**kw):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            req = httpx.Request("POST", "https://api.groq.com")
            raise groq.BadRequestError("json_validate_failed", response=httpx.Response(400, request=req), body=None)
        return original(**kw)

    p.client.chat.completions.create = criar
    assert p.gerar_json("s", "u", AnaliseIA).categoria.value == "iluminacao"
    assert chamadas["n"] == 2
