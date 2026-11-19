"""API Bairro em Dia — FastAPI.

Rodar: uvicorn app.main:app --reload  (dentro da pasta backend/)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.providers.llm import LLMError, LLMNaoConfigurado, LLMRespostaInvalida, LLMTimeout
from app.routers import assistente, relatos, sistema

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bairro_em_dia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    if cfg.seed_demo:
        from app.seed import popular_demo

        popular_demo()
    if not cfg.groq_api_key:
        log.warning("GROQ_API_KEY não definida: rotas de IA responderão 503.")
    yield


app = FastAPI(
    title="Bairro em Dia API",
    description="Relatos de problemas do bairro classificados por IA (Groq) + assistente ao cidadão.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,  # lista explícita, sem "*"
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Gestor-Token"],
)


def erro(status: int, codigo: str, mensagem: str, campos: list[str] | None = None) -> JSONResponse:
    corpo = {"codigo": codigo, "mensagem": mensagem}
    if campos:
        corpo["campos"] = campos
    return JSONResponse(status_code=status, content=corpo)


@app.exception_handler(LLMTimeout)
async def _timeout(_: Request, __: LLMTimeout):
    return erro(504, "IA_TIMEOUT", "A análise demorou mais que o esperado. Tente novamente em instantes.")


@app.exception_handler(LLMRespostaInvalida)
async def _invalida(_: Request, __: LLMRespostaInvalida):
    return erro(502, "IA_RESPOSTA_INVALIDA", "Não conseguimos interpretar a análise automática. Tente novamente.")


@app.exception_handler(LLMNaoConfigurado)
async def _sem_chave(_: Request, __: LLMNaoConfigurado):
    return erro(503, "IA_NAO_CONFIGURADA", "O serviço de IA não está disponível no momento.")


@app.exception_handler(LLMError)
async def _llm(_: Request, __: LLMError):
    return erro(502, "IA_INDISPONIVEL", "O serviço de IA está instável agora. Tente novamente em alguns minutos.")


@app.exception_handler(RequestValidationError)
async def _validacao(_: Request, exc: RequestValidationError):
    campos = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
    return erro(422, "DADOS_INVALIDOS", "Alguns campos não estão corretos.", campos)


@app.exception_handler(StarletteHTTPException)
async def _http(_: Request, exc: StarletteHTTPException):
    codigos = {401: "NAO_AUTORIZADO", 404: "NAO_ENCONTRADO", 413: "ARQUIVO_GRANDE", 415: "FORMATO_INVALIDO"}
    mensagem = exc.detail if isinstance(exc.detail, str) else "Não foi possível concluir a solicitação."
    return erro(exc.status_code, codigos.get(exc.status_code, "ERRO"), mensagem)


@app.exception_handler(Exception)
async def _generico(_: Request, exc: Exception):
    log.exception("Erro não tratado: %s", type(exc).__name__)
    return erro(500, "ERRO_INTERNO", "Algo deu errado do nosso lado. Tente novamente.")


app.include_router(sistema.router)
app.include_router(relatos.router)
app.include_router(assistente.router)
