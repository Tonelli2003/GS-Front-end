"""Fixtures: LLM falso e banco em memória — os testes rodam sem chave da Groq e sem subir a interface."""
import os

os.environ["GESTOR_TOKEN"] = "token-teste"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:8501"
os.environ["SEED_DEMO"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.llm import LLMTimeout, get_llm
from app.providers.repositorio import Repositorio, get_repositorio
from app.schemas.assistente import RespostaAssistente
from app.schemas.relato import AnaliseIA


class LLMFalso:
    def __init__(self, falhar_com: Exception | None = None, risco: bool = False):
        self.falhar_com = falhar_com
        self.risco = risco
        self.ultima_mensagem = ""

    def gerar_json(self, sistema, usuario, modelo):
        self.ultima_mensagem = usuario
        if self.falhar_com:
            raise self.falhar_com
        if modelo is AnaliseIA:
            return AnaliseIA(
                categoria="buraco_via",
                criticidade="media",
                titulo="Buraco na rua",
                resumo="Buraco na pista próximo ao número 100.",
                justificativa_criticidade="Pode causar acidente com motos.",
                orgao_responsavel="Prefeitura – manutenção viária",
                orientacao_cidadao="Sinalize o local se for seguro.",
                risco_imediato=self.risco,
                confianca=0.9,
            )
        if modelo is RespostaAssistente:
            return RespostaAssistente(
                resposta="Você pode abrir um pedido no SP156.",
                passos=["Ligue 156"],
                canais=[
                    {"nome": "SP156 (Prefeitura de São Paulo)", "como_acessar": "156", "quando_usar": "zeladoria"},
                    {"nome": "Canal Inventado", "como_acessar": "0800 000", "quando_usar": "nunca"},
                ],
                emergencia=False,
            )
        raise AssertionError("modelo inesperado")

    def descrever_imagem(self, imagem_b64, mime):
        return "Foto mostra um buraco no asfalto."

    def transcrever(self, conteudo, nome_arquivo):
        return "tem um buraco enorme aqui na rua"


@pytest.fixture
def llm():
    return LLMFalso()


@pytest.fixture
def client(llm):
    repo = Repositorio(":memory:")
    app.dependency_overrides[get_llm] = lambda: llm
    app.dependency_overrides[get_repositorio] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def relato_valido():
    return {
        "descricao": "Tem um buraco grande na rua em frente ao número 100, motos estão desviando.",
        "endereco": "Rua das Flores, 100",
        "bairro": "Vila Mariana",
        "cidade": "São Paulo",
        "cep": "04101-000",
    }


__all__ = ["LLMFalso", "LLMTimeout"]
