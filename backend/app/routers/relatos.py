from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.config import get_settings
from app.pipelines import protocolos as svc
from app.pipelines.classificacao import analisar_relato
from app.providers.llm import LLMProvider, get_llm
from app.providers.repositorio import Repositorio, get_repositorio
from app.routers.deps import exigir_gestor
from app.schemas.relato import (
    AnaliseResposta,
    AtualizacaoStatus,
    Avaliacao,
    Categoria,
    Criticidade,
    Protocolo,
    ProtocoloPublico,
    RelatoConfirmacao,
    RelatoEntrada,
    Status,
    Transcricao,
)

router = APIRouter(prefix="/relatos", tags=["relatos"])

AUDIO_TIPOS = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a",
               "audio/x-m4a", "audio/ogg", "audio/webm", "video/webm"}
AUDIO_MAX = 10 * 1024 * 1024


@router.post("/analisar", response_model=AnaliseResposta, summary="IA analisa e classifica o relato (não salva)")
def analisar(entrada: RelatoEntrada, llm: LLMProvider = Depends(get_llm)):
    return analisar_relato(entrada, llm, get_settings().groq_model)


@router.post("/transcrever", response_model=Transcricao, summary="Transcreve áudio do relato (Whisper/Groq)")
async def transcrever(arquivo: UploadFile = File(...), llm: LLMProvider = Depends(get_llm)):
    if arquivo.content_type not in AUDIO_TIPOS:
        raise HTTPException(415, "Formato de áudio não suportado. Use WAV, MP3, M4A, OGG ou WEBM.")
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(422, "O áudio está vazio.")
    if len(conteudo) > AUDIO_MAX:
        raise HTTPException(413, "O áudio deve ter no máximo 10 MB.")
    texto = llm.transcrever(conteudo, arquivo.filename or "audio.wav")
    if not texto:
        raise HTTPException(422, "Não foi possível entender o áudio. Tente gravar novamente.")
    return Transcricao(texto=texto)


@router.post("", response_model=Protocolo, status_code=201, summary="Cidadão confirma e gera protocolo")
def criar(dados: RelatoConfirmacao, repo: Repositorio = Depends(get_repositorio)):
    return svc.criar_protocolo(dados, repo)


@router.get("/publico", response_model=list[ProtocoloPublico], summary="Dados anonimizados para o painel")
def listar_publico(repo: Repositorio = Depends(get_repositorio)):
    return [svc.para_publico(p) for p in repo.listar()]


@router.get("", response_model=list[Protocolo], dependencies=[Depends(exigir_gestor)],
            summary="Lista completa (gestor)")
def listar(
    status: Status | None = Query(None),
    categoria: Categoria | None = Query(None),
    criticidade: Criticidade | None = Query(None),
    repo: Repositorio = Depends(get_repositorio),
):
    itens = repo.listar()
    if status:
        itens = [p for p in itens if p.status == status]
    if categoria:
        itens = [p for p in itens if p.categoria == categoria]
    if criticidade:
        itens = [p for p in itens if p.criticidade == criticidade]
    return itens


def _obter_ou_404(numero: str, repo: Repositorio) -> Protocolo:
    p = repo.obter(numero)
    if not p:
        raise HTTPException(404, "Protocolo não encontrado.")
    return p


@router.get("/{numero}", response_model=Protocolo, summary="Consulta de protocolo pelo número")
def obter(numero: str, repo: Repositorio = Depends(get_repositorio)):
    return _obter_ou_404(numero, repo)


@router.patch("/{numero}/status", response_model=Protocolo, dependencies=[Depends(exigir_gestor)],
              summary="Gestor atualiza o andamento")
def mudar_status(numero: str, upd: AtualizacaoStatus, repo: Repositorio = Depends(get_repositorio)):
    return svc.atualizar_status(_obter_ou_404(numero, repo), upd, repo)


@router.post("/{numero}/avaliacao", response_model=Protocolo, summary="Cidadão avalia a classificação da IA")
def avaliar(numero: str, av: Avaliacao, repo: Repositorio = Depends(get_repositorio)):
    return svc.avaliar(_obter_ou_404(numero, repo), av, repo)
