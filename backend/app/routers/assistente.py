import logging

from fastapi import APIRouter, Depends

from app.pipelines.assistente import responder
from app.providers.llm import LLMProvider, get_llm
from app.schemas.assistente import FeedbackAssistente, PerguntaAssistente, RespostaAssistente

router = APIRouter(prefix="/assistente", tags=["assistente"])
log = logging.getLogger(__name__)


@router.post("/perguntar", response_model=RespostaAssistente)
def perguntar(pergunta: PerguntaAssistente, llm: LLMProvider = Depends(get_llm)):
    return responder(pergunta, llm)


@router.post("/feedback", status_code=204)
def feedback(fb: FeedbackAssistente):
    # POC: registra em log (sem dados pessoais). Em produção iria para uma tabela de avaliação.
    log.info("feedback_assistente util=%s tamanho_pergunta=%s", fb.util, len(fb.pergunta))
