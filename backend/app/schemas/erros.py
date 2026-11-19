from pydantic import BaseModel


class ErroPadrao(BaseModel):
    """Formato único de erro devolvido ao front (sem stack trace ou detalhe técnico)."""

    codigo: str
    mensagem: str
    campos: list[str] | None = None
