from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.providers.viacep import CepIndisponivel, CepNaoEncontrado, buscar_cep
from app.routers.deps import exigir_gestor

router = APIRouter(tags=["sistema"])


@router.get("/health")
def health():
    cfg = get_settings()
    return {"status": "ok", "ia_configurada": bool(cfg.groq_api_key), "modelo": cfg.groq_model}


@router.post("/auth/gestor", dependencies=[Depends(exigir_gestor)])
def validar_gestor():
    return {"ok": True}


@router.get("/localizacao/cep/{cep}")
def cep(cep: str):
    try:
        return buscar_cep(cep)
    except CepNaoEncontrado:
        raise HTTPException(404, "CEP não encontrado. Confira os números.")
    except CepIndisponivel:
        raise HTTPException(503, "Busca de CEP indisponível no momento. Preencha o endereço manualmente.")
