import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ─────────────────────────── CONFIG ───────────────────────────
st.set_page_config(
    page_title="Painel SGD 2026 — Nacional Gás",
    page_icon="📊",
    layout="wide",
)

AZUL = "#1A3A5C"
CORES = {"Concluído": "#2E7D32", "Em andamento": "#F9A825", "Não iniciado": "#C62828"}
ORDEM_STATUS = ["Concluído", "Em andamento", "Não iniciado"]
ARQUIVO_PADRAO = "Acompanhamento_SGD_2026.xlsx"

st.markdown(f"""
<style>
    .block-container {{ padding-top: 2rem; max-width: 1400px; }}
    .kpi {{
        background:#fff; border-radius:12px; padding:16px 18px;
        box-shadow:0 1px 4px rgba(0,0,0,.08); border-left:5px solid {AZUL};
    }}
    .kpi .rotulo {{ font-size:.72rem; color:#666; text-transform:uppercase; letter-spacing:.05em; }}
    .kpi .valor  {{ font-size:1.9rem; font-weight:700; color:{AZUL}; line-height:1.15; }}
    .kpi .nota   {{ font-size:.72rem; color:#888; }}
    .meta-card {{
        background:#fff; border-radius:12px; padding:16px 18px;
        box-shadow:0 1px 4px rgba(0,0,0,.08); height:100%;
    }}
    .meta-card h4 {{ margin:0 0 2px 0; font-size:.92rem; color:{AZUL}; }}
    .meta-card .peso {{ font-size:.72rem; color:#777; margin-bottom:10px; }}
    .barra {{ height:8px; border-radius:4px; background:#eee; overflow:hidden; margin:8px 0; }}
    .barra span {{ display:block; height:100%; }}
    .selo {{ display:inline-block; padding:2px 10px; border-radius:20px;
             font-size:.7rem; font-weight:600; }}
    .marco {{ border-left:3px solid {AZUL}; padding:2px 0 14px 16px; position:relative; }}
    .marco::before {{ content:''; position:absolute; left:-7px; top:4px; width:11px; height:11px;
                      border-radius:50%; background:{AZUL}; }}
    .marco .data {{ font-size:.75rem; font-weight:700; color:{AZUL}; }}
    .marco .txt  {{ font-size:.85rem; color:#444; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── DADOS ───────────────────────────
@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def carregar_dados(origem):
    df = pd.read_excel(origem, sheet_name="Entrada")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Entregável"])
    for col in ["Meta", "Nível", "Status", "Responsável", "Prazo", "Pendência", "Evidência", "Risco"]:
        if col in df.columns:
            df[col] = df[col].fillna("—").astype(str).str.strip()
    df["Status"] = df["Status"].replace({"": "Não iniciado"})
    return df


def explodir_responsaveis(df, separar=True):
    """Separa responsáveis múltiplos ('A, B' ou 'A + B') em linhas individuais."""
    if not separar or "Responsável" not in df.columns:
        return df
    linhas = []
    for _, r in df.iterrows():
        resp = r["Responsável"]
        if resp in ("—", "", "A definir"):
            linhas.append(r)
            continue
        partes = [p.strip() for p in resp.replace(" + ", ",").split(",") if p.strip()]
        for p in partes:
            nova = r.copy()
            nova["Responsável"] = p
            linhas.append(nova)
    return pd.DataFrame(linhas)


# ─────────────────────────── SIDEBAR ───────────────────────────
with st.sidebar:
    st.markdown("### Fonte de dados")
    upload = st.file_uploader("Atualizar planilha (.xlsx)", type=["xlsx"])
    st.caption("Sem upload, o painel usa o arquivo do repositório.")

    try:
        df = carregar_dados(upload if upload else ARQUIVO_PADRAO)
    except Exception as e:
        st.error(f"Não foi possível ler a planilha: {e}")
        st.stop()

    st.divider()
    st.markdown("### Filtros")
    metas = sorted(df["Meta"].unique())
    f_meta = st.multiselect("Meta", metas, default=metas)

    niveis = [n for n in ["80%", "100%", "120%"] if n in df["Nível"].unique()]
    f_nivel = st.multiselect("Nível", niveis, default=niveis)

    f_status = st.multiselect("Status", ORDEM_STATUS, default=ORDEM_STATUS)

    st.divider()
    st.caption(f"Atualizado em {datetime.now():%d/%m/%Y %H:%M}")

# aplica filtros
dff = df[df["Meta"].isin(f_meta) & df["Nível"].isin(f_nivel) & df["Status"].isin(f_status)]


# ─────────────────────────── HEADER ───────────────────────────
st.markdown(f"## Painel SGD 2026 — Nacional Gás")
st.caption("Acompanhamento das metas até 30/11/2026 · Férias da gestora 02–22/12")

c1, c2, c3 = st.columns([1, 1, 2])
c1.markdown(f"<span class='selo' style='background:#FDECEA;color:#C62828'>Prazo fatal: 30/11/2026</span>", unsafe_allow_html=True)
c2.markdown(f"<span class='selo' style='background:#FFF4E0;color:#B26A00'>Férias: 02 a 22/12</span>", unsafe_allow_html=True)

st.divider()


# ─────────────────────────── KPIs ───────────────────────────
total = len(dff)
concluidos = (dff["Status"] == "Concluído").sum()
andamento = (dff["Status"] == "Em andamento").sum()
nao_iniciados = (dff["Status"] == "Não iniciado").sum()
taxa = (concluidos / total * 100) if total else 0

k1, k2, k3, k4, k5 = st.columns(5)
def kpi(col, rotulo, valor, nota, cor=AZUL):
    col.markdown(f"""
    <div class='kpi' style='border-left-color:{cor}'>
        <div class='rotulo'>{rotulo}</div>
        <div class='valor' style='color:{cor}'>{valor}</div>
        <div class='nota'>{nota}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "Total de entregáveis", total, "no filtro atual")
kpi(k2, "Concluídos", concluidos, f"{concluidos/total*100:.1f}% do total" if total else "—", CORES["Concluído"])
kpi(k3, "Em andamento", andamento, f"{andamento/total*100:.1f}% do total" if total else "—", CORES["Em andamento"])
kpi(k4, "Não iniciados", nao_iniciados, f"{nao_iniciados/total*100:.1f}% do total" if total else "—", CORES["Não iniciado"])
kpi(k5, "Taxa de conclusão", f"{taxa:.1f}%", "concluídos / total", CORES["Concluído"] if taxa >= 50 else CORES["Não iniciado"])

st.write("")


# ─────────────────────────── GRÁFICOS ───────────────────────────
g1, g2 = st.columns(2)

with g1:
    st.markdown("#### Entregáveis por status")
    cont = dff["Status"].value_counts().reindex(ORDEM_STATUS).fillna(0).reset_index()
    cont.columns = ["Status", "Qtd"]
    fig = px.bar(cont, x="Status", y="Qtd", color="Status",
                 color_discrete_map=CORES, text="Qtd")
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=340,
                      margin=dict(t=20, b=20, l=10, r=10),
                      plot_bgcolor="white", yaxis_title="Entregáveis", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.markdown("#### Status por meta")
    por_meta = (dff.groupby(["Meta", "Status"]).size()
                .reset_index(name="Qtd"))
    fig = px.bar(por_meta, x="Meta", y="Qtd", color="Status",
                 color_discrete_map=CORES, category_orders={"Status": ORDEM_STATUS},
                 text="Qtd")
    fig.update_traces(textposition="inside")
    fig.update_layout(barmode="stack", height=340,
                      margin=dict(t=20, b=20, l=10, r=10),
                      plot_bgcolor="white", yaxis_title="Entregáveis", xaxis_title="",
                      legend_title="", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("#### Distribuição por nível de desafio")
por_nivel = dff.groupby(["Nível", "Status"]).size().reset_index(name="Qtd")
fig = px.bar(por_nivel, x="Nível", y="Qtd", color="Status",
             color_discrete_map=CORES, category_orders={"Status": ORDEM_STATUS, "Nível": ["80%", "100%", "120%"]},
             text="Qtd")
fig.update_traces(textposition="inside")
fig.update_layout(barmode="group", height=320,
                  margin=dict(t=20, b=20, l=10, r=10),
                  plot_bgcolor="white", yaxis_title="Entregáveis", xaxis_title="",
                  legend_title="")
st.plotly_chart(fig, use_container_width=True)

st.divider()


# ─────────────────────────── CARDS DAS METAS ───────────────────────────
st.markdown("### Visão por meta")

cols = st.columns(len(metas))
for col, meta in zip(cols, metas):
    sub = df[df["Meta"] == meta]
    t = len(sub)
    c = (sub["Status"] == "Concluído").sum()
    a = (sub["Status"] == "Em andamento").sum()
    n = (sub["Status"] == "Não iniciado").sum()
    pct = (c / t * 100) if t else 0

    if pct >= 60:
        cor, selo = CORES["Concluído"], "No prazo"
    elif pct > 0:
        cor, selo = CORES["Em andamento"], "Atenção"
    else:
        cor, selo = CORES["Não iniciado"], "Crítico"

    peso = sub["Peso"].iloc[0] if "Peso" in sub.columns and len(sub) else "—"

    col.markdown(f"""
    <div class='meta-card'>
        <h4>{meta}</h4>
        <div class='peso'>Peso: {peso} · {t} entregáveis</div>
        <span class='selo' style='background:{cor}22;color:{cor}'>{selo}</span>
        <div class='barra'><span style='width:{pct:.0f}%;background:{cor}'></span></div>
        <div style='font-size:.78rem;color:#555'>
            ✅ {c} concluídos · 🟡 {a} em andamento · 🔴 {n} não iniciados
        </div>
    </div>""", unsafe_allow_html=True)

st.write("")
st.divider()


# ─────────────────────────── ANÁLISE POR RESPONSÁVEL ───────────────────────────
st.markdown("### Análise por responsável")

r1, r2 = st.columns([3, 1])
with r2:
    separar = st.checkbox(
        "Separar responsáveis múltiplos",
        value=True,
        help="Ex.: 'Caroline, Ligia, Patricia' vira 3 linhas, uma por pessoa.",
    )

df_resp = explodir_responsaveis(dff, separar)

if "Responsável" in df_resp.columns and len(df_resp):
    resumo = (
        df_resp.groupby("Responsável")["Status"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=ORDEM_STATUS, fill_value=0)
        .reset_index()
    )
    resumo["Total"] = resumo[ORDEM_STATUS].sum(axis=1)
    resumo["% Conclusão"] = (resumo["Concluído"] / resumo["Total"] * 100).round(1)
    resumo = resumo.sort_values("Total", ascending=False).reset_index(drop=True)

    # gráfico empilhado por responsável
    long = df_resp.groupby(["Responsável", "Status"]).size().reset_index(name="Qtd")
    fig = px.bar(long, x="Responsável", y="Qtd", color="Status",
                 color_discrete_map=CORES, category_orders={"Status": ORDEM_STATUS},
                 text="Qtd")
    fig.update_traces(textposition="inside")
    fig.update_layout(barmode="stack", height=380,
                      margin=dict(t=20, b=20, l=10, r=10),
                      plot_bgcolor="white", yaxis_title="Entregáveis", xaxis_title="",
                      legend_title="", xaxis_tickangle=-20)
    st.plotly_chart(fig, use_container_width=True)

    # tabela resumo
    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Responsável": st.column_config.TextColumn("Responsável", width="medium"),
            "Concluído": st.column_config.NumberColumn("Concluídos", format="%d"),
            "Em andamento": st.column_config.NumberColumn("Em andamento", format="%d"),
            "Não iniciado": st.column_config.NumberColumn("Não iniciados", format="%d"),
            "Total": st.column_config.NumberColumn("Total", format="%d"),
            "% Conclusão": st.column_config.NumberColumn("% Conclusão", format="%.1f%%"),
        },
    )

    # alerta para quem tem carga alta de não iniciados
    criticos = resumo[resumo["Não iniciado"] > 0].sort_values("Não iniciado", ascending=False)
    if len(criticos):
        st.warning(
            "**Atenção à alocação:** " +
            ", ".join(f"{r} ({n} não iniciados)" for r, n in zip(criticos["Responsável"], criticos["Não iniciado"]))
        )
else:
    st.info("Nenhum dado de responsável disponível no filtro atual.")

st.divider()


# ─────────────────────────── MARCOS E RISCOS ───────────────────────────
m1, m2 = st.columns([1, 1])

with m1:
    st.markdown("### Marcos críticos")
    marcos = [
        ("22/10/2026", "Reunião de votação do Manual de Padronização com os revendedores"),
        ("23/10/2026", "Entrega da proposta de fluxo de acompanhamento"),
        ("30/11/2026", "Prazo final de encaminhamento de todas as entregas"),
        ("02–22/12/2026", "Férias da gestora — sem validação de relatórios"),
    ]
    for d, t in marcos:
        st.markdown(f"<div class='marco'><div class='data'>{d}</div><div class='txt'>{t}</div></div>",
                    unsafe_allow_html=True)

with m2:
    st.markdown("### Riscos prioritários")
    st.error("**Votação de 22/10 (Meta 1)** — se o manual for reprovado novamente, os níveis 100% e 120% ficam inviáveis em 2026.")
    st.warning("**Nível 120%** — todos os entregáveis de superação estão não iniciados e a maioria sem responsável definido.")
    st.warning("**Governança (Metas 2 e 3)** — ferramenta de controle indefinida e escopo Hoodu/Goya pendente de aprovação.")
    st.error("**Meta 4 sem liderança** — entregáveis com responsável 'A definir' e dependência do cronograma da Califórnia.")

st.divider()


# ─────────────────────────── TABELA ───────────────────────────
st.markdown("### Repositório de entregáveis")

colunas = [c for c in ["Meta", "Nível", "Entregável", "Status", "Responsável", "Prazo", "Pendência", "Risco"]
           if c in dff.columns]

st.dataframe(
    dff[colunas].sort_values(["Meta", "Nível", "Status"]),
    use_container_width=True,
    hide_index=True,
    height=460,
    column_config={
        "Status": st.column_config.TextColumn("Status", width="small"),
        "Nível": st.column_config.TextColumn("Nível", width="small"),
        "Entregável": st.column_config.TextColumn("Entregável", width="large"),
    },
)

st.download_button(
    "⬇️ Baixar dados filtrados (.csv)",
    dff[colunas].to_csv(index=False).encode("utf-8-sig"),
    file_name="sgd_2026_filtrado.csv",
    mime="text/csv",
)