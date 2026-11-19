"""Popula o banco com relatos FICTÍCIOS de demonstração (marcados demo=True) para o painel.

Uso: python -m app.seed   (ou SEED_DEMO=true no .env)
"""
import random
from datetime import datetime, timedelta, timezone

from app.providers.base_conhecimento import ORGAOS_POR_CATEGORIA
from app.providers.repositorio import get_repositorio
from app.schemas.relato import Categoria, Criticidade, EventoStatus, Protocolo, Status

BAIRROS = ["Vila Mariana", "Capão Redondo", "Itaquera", "Lapa", "Brasilândia", "Mooca", "Grajaú", "Santana"]
EXEMPLOS = {
    Categoria.BURACO: "Buraco grande na pista perto do ponto de ônibus",
    Categoria.ILUMINACAO: "Poste apagado há uma semana, rua fica escura",
    Categoria.LIXO: "Lixo e entulho acumulados na esquina",
    Categoria.RUIDO: "Som alto de bar até de madrugada",
    Categoria.AGUA_ESGOTO: "Esgoto vazando na calçada",
    Categoria.ARVORE: "Árvore com galho quebrado pendurado",
    Categoria.CALCADA: "Calçada quebrada impede passagem de cadeira de rodas",
    Categoria.OUTRO: "Placa de rua caída",
}
PESOS_CAT = [18, 16, 20, 10, 8, 8, 8, 4]
PESOS_CRIT = [25, 40, 25, 10]


def popular_demo(qtd: int = 60, semente: int = 42) -> int:
    repo = get_repositorio()
    if repo.contar() > 0:
        return 0
    rnd = random.Random(semente)
    hoje = datetime.now(timezone.utc)
    for _ in range(qtd):
        cat = rnd.choices(list(Categoria), PESOS_CAT)[0]
        crit = rnd.choices(list(Criticidade), PESOS_CRIT)[0]
        criado = hoje - timedelta(days=rnd.randint(0, 45), hours=rnd.randint(0, 23))
        status = rnd.choices(list(Status), [30, 20, 25, 20, 5])[0]
        corrigido = rnd.random() < 0.12
        p = Protocolo(
            numero=repo.proximo_numero(),
            criado_em=criado,
            atualizado_em=criado,
            status=status,
            categoria=cat,
            criticidade=crit,
            titulo=EXEMPLOS[cat],
            resumo=f"[DEMO] {EXEMPLOS[cat]}.",
            descricao=f"[DEMO] {EXEMPLOS[cat]}.",
            endereco="Endereço fictício de demonstração",
            bairro=rnd.choice(BAIRROS),
            cidade="São Paulo",
            orgao_responsavel=ORGAOS_POR_CATEGORIA[cat.value],
            orientacao_cidadao="Acompanhe pelo número do protocolo.",
            risco_imediato=crit == Criticidade.URGENTE,
            tem_foto=rnd.random() < 0.5,
            tem_audio=rnd.random() < 0.2,
            categoria_sugerida_ia=Categoria.OUTRO if corrigido else cat,
            criticidade_sugerida_ia=crit,
            corrigido_pelo_cidadao=corrigido,
            historico=[EventoStatus(status=status, data=criado)],
            demo=True,
        )
        repo.salvar(p)
    return qtd


if __name__ == "__main__":
    print(f"{popular_demo()} relatos de demonstração criados.")
