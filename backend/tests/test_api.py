from app.main import app
from app.providers.llm import LLMRespostaInvalida, LLMTimeout, get_llm
from tests.conftest import LLMFalso

GESTOR = {"X-Gestor-Token": "token-teste"}


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_analisar_retorna_saida_estruturada(client, relato_valido):
    r = client.post("/relatos/analisar", json=relato_valido)
    assert r.status_code == 200
    analise = r.json()["analise"]
    assert analise["categoria"] == "buraco_via"
    assert analise["criticidade"] in {"baixa", "media", "alta", "urgente"}


def test_validacao_descricao_curta(client, relato_valido):
    relato_valido["descricao"] = "buraco"
    r = client.post("/relatos/analisar", json=relato_valido)
    assert r.status_code == 422
    assert r.json()["codigo"] == "DADOS_INVALIDOS"
    assert "descricao" in r.json()["campos"]


def test_cep_invalido_rejeitado(client, relato_valido):
    relato_valido["cep"] = "123"
    assert client.post("/relatos/analisar", json=relato_valido).status_code == 422


def test_timeout_da_ia_vira_mensagem_amigavel(client, relato_valido):
    app.dependency_overrides[get_llm] = lambda: LLMFalso(falhar_com=LLMTimeout())
    r = client.post("/relatos/analisar", json=relato_valido)
    assert r.status_code == 504
    assert r.json()["codigo"] == "IA_TIMEOUT"
    assert "Traceback" not in r.text


def test_resposta_invalida_da_ia(client, relato_valido):
    app.dependency_overrides[get_llm] = lambda: LLMFalso(falhar_com=LLMRespostaInvalida("x"))
    r = client.post("/relatos/analisar", json=relato_valido)
    assert r.status_code == 502 and r.json()["codigo"] == "IA_RESPOSTA_INVALIDA"


def _criar(client, relato, categoria_final="buraco_via"):
    analise = client.post("/relatos/analisar", json=relato).json()["analise"]
    payload = {**relato, "analise_ia": analise, "categoria_final": categoria_final,
               "criticidade_final": analise["criticidade"]}
    return client.post("/relatos", json=payload)


def test_fluxo_completo_com_correcao_humana(client, relato_valido):
    r = _criar(client, relato_valido, categoria_final="calcada_acessibilidade")
    assert r.status_code == 201
    p = r.json()
    assert p["numero"].startswith("BED-")
    assert p["corrigido_pelo_cidadao"] is True
    assert p["categoria_sugerida_ia"] == "buraco_via"
    assert client.get(f"/relatos/{p['numero']}").status_code == 200


def test_painel_publico_nao_expoe_endereco(client, relato_valido):
    _criar(client, relato_valido)
    item = client.get("/relatos/publico").json()[0]
    assert "endereco" not in item and "descricao" not in item


def test_rotas_de_gestor_exigem_token(client, relato_valido):
    numero = _criar(client, relato_valido).json()["numero"]
    assert client.get("/relatos").status_code == 401
    assert client.patch(f"/relatos/{numero}/status", json={"status": "resolvido"}).status_code == 401
    r = client.patch(f"/relatos/{numero}/status", json={"status": "resolvido", "observacao": "ok"}, headers=GESTOR)
    assert r.status_code == 200 and r.json()["status"] == "resolvido"
    assert len(r.json()["historico"]) == 2


def test_avaliacao_do_cidadao(client, relato_valido):
    numero = _criar(client, relato_valido).json()["numero"]
    r = client.post(f"/relatos/{numero}/avaliacao", json={"avaliacao": "incorreta", "comentario": "não é buraco"})
    assert r.json()["avaliacao"] == "incorreta"


def test_protocolo_inexistente(client):
    r = client.get("/relatos/BED-2000-999999")
    assert r.status_code == 404 and r.json()["codigo"] == "NAO_ENCONTRADO"


def test_cors_restritivo(client):
    ok = client.options("/health", headers={"Origin": "http://localhost:8501", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8501"
    ruim = client.options("/health", headers={"Origin": "http://site-malicioso.com", "Access-Control-Request-Method": "GET"})
    assert ruim.headers.get("access-control-allow-origin") is None


def test_transcricao_formato_invalido(client):
    r = client.post("/relatos/transcrever", files={"arquivo": ("a.txt", b"abc", "text/plain")})
    assert r.status_code == 415


def test_transcricao_ok(client):
    r = client.post("/relatos/transcrever", files={"arquivo": ("a.wav", b"RIFF....", "audio/wav")})
    assert r.status_code == 200 and "buraco" in r.json()["texto"]


def test_assistente_filtra_canal_inventado(client):
    r = client.post("/assistente/perguntar", json={"pergunta": "Como peço tapa-buraco?"})
    nomes = [c["nome"] for c in r.json()["canais"]]
    assert nomes == ["SP156 (Prefeitura de São Paulo)"]
