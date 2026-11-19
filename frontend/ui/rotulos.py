"""Rótulos em linguagem simples + cores semânticas (sempre acompanhadas de ícone e texto)."""

CATEGORIAS = {
    "buraco_via": ("🕳️", "Buraco na rua"),
    "iluminacao": ("💡", "Iluminação pública"),
    "lixo_entulho": ("🗑️", "Lixo ou entulho"),
    "ruido": ("🔊", "Barulho / incômodo sonoro"),
    "agua_esgoto": ("🚰", "Água ou esgoto"),
    "arvore_area_verde": ("🌳", "Árvore / área verde"),
    "calcada_acessibilidade": ("♿", "Calçada / acessibilidade"),
    "outro": ("📌", "Outro problema"),
}

# Cores escuras o bastante para texto branco com contraste >= 4.5:1 (WCAG AA)
CRITICIDADES = {
    "baixa": ("🟢", "Baixa", "#1B6E35"),
    "media": ("🟡", "Média", "#7A5300"),
    "alta": ("🟠", "Alta", "#A63F00"),
    "urgente": ("🔴", "Urgente", "#A3001B"),
}

STATUS = {
    "recebido": ("📥", "Recebido"),
    "em_analise": ("🔎", "Em análise"),
    "encaminhado": ("📤", "Encaminhado ao órgão"),
    "resolvido": ("✅", "Resolvido"),
    "recusado": ("⛔", "Não atendido"),
}

ORDEM_CRITICIDADE = list(CRITICIDADES)


def categoria_txt(valor: str) -> str:
    icone, nome = CATEGORIAS.get(valor, ("📌", valor))
    return f"{icone} {nome}"


def criticidade_txt(valor: str) -> str:
    icone, nome, _ = CRITICIDADES.get(valor, ("⚪", valor, "#444"))
    return f"{icone} {nome}"


def status_txt(valor: str) -> str:
    icone, nome = STATUS.get(valor, ("•", valor))
    return f"{icone} {nome}"
