"""Lista os modelos que a sua GROQ_API_KEY consegue usar.

Uso (dentro de backend/): python -m scripts.listar_modelos
"""
from app.config import get_settings


def main() -> None:
    cfg = get_settings()
    if not cfg.groq_api_key:
        print("GROQ_API_KEY não encontrada no .env")
        return
    import groq

    ids = sorted(m.id for m in groq.Groq(api_key=cfg.groq_api_key).models.list().data)
    print("Modelos disponíveis:\n  " + "\n  ".join(ids))
    for nome, valor in (("GROQ_MODEL", cfg.groq_model), ("GROQ_VISION_MODEL", cfg.groq_vision_model),
                        ("GROQ_STT_MODEL", cfg.groq_stt_model)):
        print(f"{nome}={valor} -> {'OK' if valor in ids else 'NÃO DISPONÍVEL'}")


if __name__ == "__main__":
    main()
