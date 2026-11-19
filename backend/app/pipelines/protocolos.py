"""Regras de negócio de protocolos (criação, status, avaliação). Sem IA."""
from datetime import datetime, timezone

from app.providers.repositorio import Repositorio
from app.schemas.relato import (
    AtualizacaoStatus,
    Avaliacao,
    EventoStatus,
    Protocolo,
    ProtocoloPublico,
    RelatoConfirmacao,
    Status,
)


def agora() -> datetime:
    return datetime.now(timezone.utc)


def criar_protocolo(dados: RelatoConfirmacao, repo: Repositorio) -> Protocolo:
    ia = dados.analise_ia
    momento = agora()
    corrigido = dados.categoria_final != ia.categoria or dados.criticidade_final != ia.criticidade
    p = Protocolo(
        numero=repo.proximo_numero(),
        criado_em=momento,
        atualizado_em=momento,
        status=Status.RECEBIDO,
        categoria=dados.categoria_final,
        criticidade=dados.criticidade_final,
        titulo=ia.titulo,
        resumo=ia.resumo,
        descricao=dados.descricao,
        endereco=dados.endereco,
        bairro=dados.bairro,
        cidade=dados.cidade,
        orgao_responsavel=ia.orgao_responsavel,
        orientacao_cidadao=ia.orientacao_cidadao,
        risco_imediato=ia.risco_imediato,
        tem_foto=dados.tem_foto,
        tem_audio=dados.tem_audio,
        categoria_sugerida_ia=ia.categoria,
        criticidade_sugerida_ia=ia.criticidade,
        corrigido_pelo_cidadao=corrigido,
        historico=[EventoStatus(status=Status.RECEBIDO, data=momento, observacao="Relato registrado pelo morador")],
    )
    return repo.salvar(p)


def atualizar_status(p: Protocolo, upd: AtualizacaoStatus, repo: Repositorio) -> Protocolo:
    momento = agora()
    p.status = upd.status
    p.atualizado_em = momento
    p.historico.append(EventoStatus(status=upd.status, data=momento, observacao=upd.observacao))
    return repo.salvar(p)


def avaliar(p: Protocolo, av: Avaliacao, repo: Repositorio) -> Protocolo:
    p.avaliacao = av.avaliacao
    p.comentario_avaliacao = av.comentario
    p.atualizado_em = agora()
    return repo.salvar(p)


def para_publico(p: Protocolo) -> ProtocoloPublico:
    return ProtocoloPublico(**p.model_dump(include=set(ProtocoloPublico.model_fields)))
