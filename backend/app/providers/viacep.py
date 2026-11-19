"""Fonte de dados aberta: ViaCEP (https://viacep.com.br) para completar o endereço pelo CEP."""
import re

import httpx


class CepNaoEncontrado(Exception):
    pass


class CepIndisponivel(Exception):
    pass


def buscar_cep(cep: str) -> dict:
    digitos = re.sub(r"\D", "", cep)
    if len(digitos) != 8:
        raise CepNaoEncontrado(cep)
    try:
        r = httpx.get(f"https://viacep.com.br/ws/{digitos}/json/", timeout=5)
        r.raise_for_status()
        dados = r.json()
    except (httpx.HTTPError, ValueError) as e:
        raise CepIndisponivel(str(e)) from e
    if dados.get("erro"):
        raise CepNaoEncontrado(cep)
    return {
        "cep": f"{digitos[:5]}-{digitos[5:]}",
        "logradouro": dados.get("logradouro", ""),
        "bairro": dados.get("bairro", ""),
        "cidade": dados.get("localidade", ""),
        "uf": dados.get("uf", ""),
    }
