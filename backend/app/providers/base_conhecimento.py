"""Base de conhecimento curada de canais de atendimento (foco: estado de São Paulo).

O assistente só pode recomendar canais que estejam aqui (grounding), o que reduz alucinação
de telefones e sites. ATENÇÃO: revise estes dados periodicamente nos sites oficiais.
"""

CANAIS = [
    {
        "nome": "SP156 (Prefeitura de São Paulo)",
        "como_acessar": "Telefone 156, app SP156 ou site sp156.prefeitura.sp.gov.br",
        "quando_usar": "Capital paulista: tapa-buraco, iluminação pública apagada, limpeza urbana, "
        "remoção de entulho, poda de árvore, calçadas e barulho de estabelecimentos (PSIU).",
    },
    {
        "nome": "Ouvidoria ou central da prefeitura do seu município",
        "como_acessar": "Site oficial da prefeitura da sua cidade (geralmente seção 'Ouvidoria' ou 'Fale Conosco')",
        "quando_usar": "Cidades fora da capital: zeladoria, iluminação pública, limpeza e calçadas.",
    },
    {
        "nome": "Polícia Militar",
        "como_acessar": "Telefone 190",
        "quando_usar": "Perturbação do sossego acontecendo agora (som alto, festa), principalmente à noite, "
        "ou qualquer situação de segurança.",
    },
    {
        "nome": "Corpo de Bombeiros",
        "como_acessar": "Telefone 193",
        "quando_usar": "Árvore caída sobre fios, casas ou pessoas, incêndio, fios elétricos rompidos no chão.",
    },
    {
        "nome": "Defesa Civil",
        "como_acessar": "Telefone 199",
        "quando_usar": "Risco de desabamento, deslizamento, alagamento ou árvore com risco de queda.",
    },
    {
        "nome": "SAMU",
        "como_acessar": "Telefone 192",
        "quando_usar": "Alguém se feriu (por exemplo, caiu em um buraco) e precisa de atendimento médico.",
    },
    {
        "nome": "Sabesp",
        "como_acessar": "0800 055 0195 ou agência virtual no site da Sabesp",
        "quando_usar": "Vazamento de água, falta de água ou esgoto vazando na rua (municípios atendidos pela Sabesp).",
    },
    {
        "nome": "Distribuidora de energia elétrica",
        "como_acessar": "Telefone impresso na sua conta de luz (na capital, Enel SP)",
        "quando_usar": "Falta de energia na casa/rua ou fio de energia caído. Lâmpada de poste apagada é com a prefeitura.",
    },
]

ORGAOS_POR_CATEGORIA = {
    "buraco_via": "Prefeitura – manutenção viária (SP156 na capital)",
    "iluminacao": "Prefeitura – iluminação pública (SP156 na capital)",
    "lixo_entulho": "Prefeitura – limpeza urbana (SP156 na capital)",
    "ruido": "PSIU via SP156 (estabelecimentos) ou PM 190 (ocorrência em andamento)",
    "agua_esgoto": "Concessionária de saneamento (Sabesp, onde houver)",
    "arvore_area_verde": "Prefeitura – áreas verdes; Defesa Civil 199 se houver risco",
    "calcada_acessibilidade": "Prefeitura – fiscalização de calçadas (SP156 na capital)",
    "outro": "Prefeitura – ouvidoria municipal",
}


def canais_como_texto() -> str:
    return "\n".join(f"- {c['nome']} | {c['como_acessar']} | {c['quando_usar']}" for c in CANAIS)
