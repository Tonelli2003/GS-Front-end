"""Gráficos Plotly reutilizáveis (painel público, gestor e 'Meus protocolos')."""
import pandas as pd
import plotly.express as px

from ui.rotulos import CATEGORIAS, CRITICIDADES, ORDEM_CRITICIDADE, STATUS

CORES_CRIT = {f"{v[0]} {v[1]}": v[2] for v in CRITICIDADES.values()}
ORDEM_CRIT_TXT = [f"{CRITICIDADES[c][0]} {CRITICIDADES[c][1]}" for c in ORDEM_CRITICIDADE]


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["criado_em"] = pd.to_datetime(df["criado_em"], utc=True, format="ISO8601").dt.tz_convert("America/Sao_Paulo")
    df["dia"] = df["criado_em"].dt.date
    df["Categoria"] = df["categoria"].map(lambda v: " ".join(CATEGORIAS.get(v, ("", v))))
    df["Criticidade"] = df["criticidade"].map(lambda v: f"{CRITICIDADES[v][0]} {CRITICIDADES[v][1]}")
    df["Situação"] = df["status"].map(lambda v: " ".join(STATUS.get(v, ("", v))))
    return df


def _layout(fig, titulo: str, altura: int):
    fig.update_layout(
        title=titulo, height=altura, margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="", hoverlabel=dict(font_size=14),
    )
    return fig


def barras_por_categoria(df: pd.DataFrame, titulo: str = "Relatos por tipo de problema", altura: int = 420):
    """Barras empilhadas por criticidade (cores semânticas + legenda com ícone e texto)."""
    agg = df.groupby(["Categoria", "Criticidade"]).size().reset_index(name="Relatos")
    fig = px.bar(
        agg, x="Relatos", y="Categoria", color="Criticidade", orientation="h",
        color_discrete_map=CORES_CRIT, category_orders={"Criticidade": ORDEM_CRIT_TXT},
        hover_data={"Relatos": True},
    )
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _layout(fig, titulo, altura)


def linha_do_tempo(df: pd.DataFrame, titulo: str = "Novos relatos por dia", altura: int = 360):
    agg = df.groupby("dia").size().reset_index(name="Relatos")
    fig = px.line(agg, x="dia", y="Relatos", markers=True)
    fig.update_xaxes(title="", rangeslider_visible=True)
    return _layout(fig, titulo, altura)


def rosca_status(df: pd.DataFrame, titulo: str = "Situação dos protocolos", altura: int = 360):
    agg = df.groupby("Situação").size().reset_index(name="Relatos")
    fig = px.pie(agg, names="Situação", values="Relatos", hole=0.5)
    fig.update_traces(textinfo="label+percent", textposition="outside")
    return _layout(fig, titulo, altura)
