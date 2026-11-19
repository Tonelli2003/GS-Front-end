"""Acesso ao LLM (Groq). Único ponto do sistema que fala com o provedor de IA.

O front-end NUNCA chama a Groq: ele chama a API FastAPI, que chama este provider.
"""
import json
import logging
import re
from functools import lru_cache
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def _limpar_saida(texto: str | None) -> str:
    """Remove blocos de raciocínio (<think>) que alguns modelos incluem na resposta."""
    return _RE_THINK.sub("", texto or "").strip()


class LLMError(Exception):
    """Falha genérica do provedor de IA."""


class LLMTimeout(LLMError):
    """O provedor demorou além do limite."""


class LLMRespostaInvalida(LLMError):
    """O modelo respondeu fora do formato exigido mesmo após nova tentativa."""


class _JsonRejeitado(LLMError):
    """A Groq recusou a geração porque o modelo produziu JSON malformado (erro 400 json_validate_failed)."""


class LLMNaoConfigurado(LLMError):
    """GROQ_API_KEY ausente."""


class LLMProvider(Protocol):
    def gerar_json(self, sistema: str, usuario: str, modelo: type[T]) -> T: ...
    def descrever_imagem(self, imagem_b64: str, mime: str) -> str: ...
    def transcrever(self, conteudo: bytes, nome_arquivo: str) -> str: ...


class GroqProvider:
    def __init__(self) -> None:
        cfg = get_settings()
        if not cfg.groq_api_key:
            raise LLMNaoConfigurado("GROQ_API_KEY não configurada")
        import groq  # import tardio: testes rodam sem a lib configurada

        self._groq = groq
        self.cfg = cfg
        self.client = groq.Groq(api_key=cfg.groq_api_key, timeout=cfg.llm_timeout, max_retries=1)

    # ---------- utilitário de erros ----------
    def _chamar(self, fn, **kwargs):
        g = self._groq
        try:
            return fn(**kwargs)
        except g.APITimeoutError as e:
            raise LLMTimeout("timeout no provedor") from e
        except g.BadRequestError as e:
            if "json_validate_failed" in (getattr(e, "message", "") or str(e)):
                log.info("Groq rejeitou JSON malformado (modelo=%s); tentando de novo", kwargs.get("model"))
                raise _JsonRejeitado("json_validate_failed") from e
            log.warning("Erro Groq BadRequest (modelo=%s): %s", kwargs.get("model"), str(e)[:300])
            raise LLMError("BadRequestError") from e
        except g.APIError as e:  # conexão, rate limit, autenticação, modelo inexistente, 5xx...
            detalhe = getattr(e, "message", "") or str(e)
            log.warning("Erro Groq %s (modelo=%s): %s", type(e).__name__, kwargs.get("model"), detalhe[:300])
            if isinstance(e, g.NotFoundError):
                log.warning("Modelo indisponível na sua conta. Rode 'python -m scripts.listar_modelos' "
                            "e ajuste GROQ_MODEL / GROQ_VISION_MODEL no .env.")
            raise LLMError(type(e).__name__) from e

    def _extras_raciocinio(self, modelo: str) -> dict:
        """Modelos de raciocínio: esforço baixo (mais rápido) e raciocínio fora do conteúdo."""
        if modelo.startswith("openai/gpt-oss"):
            return {"reasoning_effort": "low"}
        if modelo.startswith("qwen/"):
            return {"reasoning_format": "hidden"}
        return {}

    # ---------- saída estruturada ----------
    def gerar_json(self, sistema: str, usuario: str, modelo: type[T]) -> T:
        schema = json.dumps(modelo.model_json_schema(), ensure_ascii=False)
        mensagens = [
            {
                "role": "system",
                "content": f"{sistema}\n\nResponda SOMENTE com um objeto JSON válido que siga "
                f"exatamente este JSON Schema (sem texto fora do JSON):\n{schema}",
            },
            {"role": "user", "content": usuario},
        ]
        ultimo_erro = ""
        for tentativa in range(3):  # 1 tentativa + até 2 correções
            try:
                resp = self._chamar(
                    self.client.chat.completions.create,
                    model=self.cfg.groq_model,
                    messages=mensagens,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_completion_tokens=4000,  # folga para o raciocínio interno + JSON
                    **self._extras_raciocinio(self.cfg.groq_model),
                )
            except _JsonRejeitado:
                ultimo_erro = "JSON malformado rejeitado pelo provedor"
                continue
            conteudo = _limpar_saida(resp.choices[0].message.content)
            try:
                return modelo.model_validate_json(conteudo)
            except ValidationError as e:
                ultimo_erro = str(e)[:800]
                log.info("Resposta fora do schema (tentativa %s)", tentativa + 1)
                mensagens += [
                    {"role": "assistant", "content": conteudo},
                    {
                        "role": "user",
                        "content": "Seu JSON não respeitou o schema. Erros:\n"
                        f"{ultimo_erro}\nDevolva o JSON corrigido.",
                    },
                ]
        raise LLMRespostaInvalida(ultimo_erro)

    # ---------- visão (foto do problema) ----------
    def descrever_imagem(self, imagem_b64: str, mime: str) -> str:
        resp = self._chamar(
            self.client.chat.completions.create,
            model=self.cfg.groq_vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Descreva objetivamente, em português e em até 3 frases, o problema "
                            "urbano visível nesta foto (ex.: buraco, lixo, poste apagado, árvore caída). "
                            "Não identifique pessoas, rostos ou placas de veículos.",
                        },
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{imagem_b64}"}},
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=1500,
            **self._extras_raciocinio(self.cfg.groq_vision_model),
        )
        return _limpar_saida(resp.choices[0].message.content)

    # ---------- áudio ----------
    def transcrever(self, conteudo: bytes, nome_arquivo: str) -> str:
        resp = self._chamar(
            self.client.audio.transcriptions.create,
            file=(nome_arquivo, conteudo),
            model=self.cfg.groq_stt_model,
            language="pt",
            temperature=0.0,
        )
        return (getattr(resp, "text", "") or "").strip()


@lru_cache
def _provider_singleton() -> GroqProvider:
    return GroqProvider()


def get_llm() -> LLMProvider:
    """Dependência FastAPI (sobrescrita nos testes por um LLM falso)."""
    return _provider_singleton()
