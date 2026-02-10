import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAMDA Estoque",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State Init ───────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "fisico" not in st.session_state:
    st.session_state.fisico = {}
if "last_upload" not in st.session_state:
    st.session_state.last_upload = None

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;500;700;900&display=swap');

    .stApp {
        background: #0a0f1a;
        color: #e0e6ed;
        font-family: 'Outfit', sans-serif;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding: 0.5rem 0.8rem !important;
        max-width: 100% !important;
    }

    .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 1.6rem;
        background: linear-gradient(135deg, #00d68f, #00b887);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0.3rem 0;
    }
    .sub-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #4a5568;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .stat-row {
        display: flex;
        gap: 6px;
        margin-bottom: 0.5rem;
    }
    .stat-card {
        flex: 1;
        background: linear-gradient(135deg, #111827, #1a2332);
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 8px 10px;
        text-align: center;
    }
    .stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.2rem;
        font-weight: 700;
        color: #00d68f;
    }
    .stat-value.red { color: #ff4757; }
    .stat-label {
        font-size: 0.6rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .prod-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 6px;
    }
    .prod-card.divergent {
        border-color: #ff4757;
        background: linear-gradient(135deg, #1a0a0d, #111827);
    }
    .prod-card.ok { border-color: #00d68f33; }
    .prod-name {
        font-size: 0.8rem;
        font-weight: 700;
        color: #e0e6ed;
        margin-bottom: 2px;
    }
    .prod-info {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #64748b;
    }
    .prod-info .sys { color: #4a90d9; }
    .prod-info .fis { color: #00d68f; }
    .prod-info .fis.bad { color: #ff4757; }
    .prod-info .diff { color: #ff4757; font-weight: 700; }

    .stRadio > div {
        flex-direction: row !important;
        gap: 4px !important;
        flex-wrap: wrap;
        justify-content: center;
    }
    .stRadio > div > label {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 20px !important;
        padding: 4px 14px !important;
        font-size: 0.75rem !important;
        color: #94a3b8 !important;
    }

    .stNumberInput input {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        color: #e0e6ed !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .div-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
    }
    .div-table th {
        background: #111827;
        color: #64748b;
        padding: 6px 8px;
        text-align: left;
        border-bottom: 1px solid #1e293b;
        text-transform: uppercase;
    }
    .div-table td {
        padding: 5px 8px;
        border-bottom: 1px solid #0d1420;
    }

    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────────────────────────────

def classify_product(name: str) -> str:
    n = name.upper()
    for cat, keyword in [("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"),
                          ("INSETICIDAS", "INSETICIDA"), ("NEMATICIDAS", "NEMATICIDA")]:
        if keyword in n:
            return cat
    return "OUTROS"


def short_name(prod: str) -> str:
    parts = prod.split(" ", 1)
    return parts[-1] if len(parts) > 1 else prod


def parse_excel(uploaded_file) -> pd.DataFrame:
    """Parse CAMDA BI Excel format with robust column detection."""
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception as e:
        st.error(f"❌ Erro ao ler o arquivo: {e}")
        return pd.DataFrame()

    # Find header row containing 'Produto'
    header_idx = None
    for i, row in df_raw.iterrows():
        vals = row.astype(str).str.upper().tolist()
        if any("PRODUTO" in v for v in vals):
            header_idx = i
            break

    if header_idx is None:
        # Fallback: try to find any row with column-like names
        for i, row in df_raw.iterrows():
            vals = row.astype(str).str.upper().tolist()
            if any("QUANTIDADE" in v or "QTD" in v for v in vals):
                header_idx = i
                break

    if header_idx is None:
        st.error("❌ Não encontrei as colunas 'Produto' e 'Quantidade' na planilha.")
        st.info("💡 Verifique se o arquivo é o relatório do BI com o estoque.")
        return pd.DataFrame()

    df = df_raw.iloc[header_idx + 1:].copy()
    raw_cols = df_raw.iloc[header_idx].tolist()
    df.columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(raw_cols)]

    # Map columns flexibly
    col_produto = None
    col_qtd = None
    col_codigo = None

    for c in df.columns:
        cu = c.upper()
        if "PRODUTO" in cu and col_produto is None:
            col_produto = c
        elif ("QUANTIDADE" in cu or cu == "QTD") and col_qtd is None:
            col_qtd = c
        elif ("CÓDIGO" in cu or "CODIGO" in cu or cu == "CÓD") and col_codigo is None:
            col_codigo = c

    if col_produto is None or col_qtd is None:
        st.error(f"❌ Colunas encontradas: {list(df.columns)} — faltou 'Produto' ou 'Quantidade'.")
        return pd.DataFrame()

    result = pd.DataFrame()
    result["Produto"] = df[col_produto].astype(str).str.strip()
    result["Qtd_Sistema"] = pd.to_numeric(df[col_qtd], errors="coerce")
    result["Codigo"] = df[col_codigo].astype(str).str.strip() if col_codigo else ""

    # Clean
    result = result.dropna(subset=["Qtd_Sistema"])
    result = result[result["Produto"].str.upper().str.strip() != ""]
    result = result[~result["Produto"].str.upper().isin(["SUM", "TOTAL", "NAN", "NONE"])]
    result = result[result["Qtd_Sistema"] > 0]
    result["Qtd_Sistema"] = result["Qtd_Sistema"].astype(int)
    result["Categoria"] = result["Produto"].apply(classify_product)

    # Stable key by code (survives name changes between reports)
    result["Chave"] = result.apply(
        lambda r: r["Codigo"] if r["Codigo"] not in ["", "nan", "None"] else r["Produto"],
        axis=1,
    )

    result = result.reset_index(drop=True)
    return result


def build_treemap(df: pd.DataFrame, fisico: dict, filter_cat: str = "TODOS"):
    if filter_cat != "TODOS":
        df = df[df["Categoria"] == filter_cat]
    if df.empty:
        return None

    labels, parents, values, colors, custom_text = [], [], [], [], []

    labels.append("ESTOQUE CAMDA")
    parents.append("")
    values.append(0)
    colors.append("#1a2332")
    custom_text.append("")

    for cat in sorted(df["Categoria"].unique()):
        labels.append(cat)
        parents.append("ESTOQUE CAMDA")
        values.append(0)
        colors.append("#1a2332")
        custom_text.append("")

    for _, row in df.iterrows():
        chave = row["Chave"]
        qtd_sys = int(row["Qtd_Sistema"])
        qtd_fis = fisico.get(chave, None)

        sn = short_name(str(row["Produto"]))
        if len(sn) > 22:
            sn = sn[:20] + "…"

        labels.append(sn)
        parents.append(row["Categoria"])
        values.append(max(qtd_sys, 1))

        if qtd_fis is None:
            colors.append("#2d6a4f")
            custom_text.append(f"Sis: {qtd_sys} · ⬜")
        elif qtd_fis == qtd_sys:
            colors.append("#00d68f")
            custom_text.append(f"✓ {qtd_sys}")
        else:
            diff = qtd_fis - qtd_sys
            colors.append("#ff4757")
            custom_text.append(f"Sis:{qtd_sys} Fís:{qtd_fis} ({diff:+d})")

    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        marker=dict(colors=colors, line=dict(width=1.5, color="#0a0f1a")),
        textinfo="label+text", text=custom_text,
        textfont=dict(family="JetBrains Mono, monospace", size=11),
        hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        pathbar=dict(visible=True, textfont=dict(family="Outfit", size=11, color="#64748b"),
                     thickness=20, edgeshape=">"),
        tiling=dict(packing="squarify", pad=3),
        branchvalues="total",
    ))
    fig.update_layout(
        paper_bgcolor="#0a0f1a", plot_bgcolor="#0a0f1a",
        margin=dict(t=5, l=2, r=2, b=2), height=520,
        font=dict(family="Outfit", color="#e0e6ed"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">MAPA DE CALOR · QUIRINÓPOLIS</div>', unsafe_allow_html=True)

# ── Upload ───────────────────────────────────────────────────────────────────
with st.expander("📤 Atualizar Planilha do BI", expanded=(st.session_state.df is None)):
    uploaded = st.file_uploader(
        "Arraste o XLSX do BI aqui",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        # Only parse if it's a new file
        if st.session_state.last_upload != uploaded.name:
            with st.spinner("🔄 Lendo planilha..."):
                df_new = parse_excel(uploaded)
            if not df_new.empty:
                st.session_state.df = df_new
                st.session_state.last_upload = uploaded.name
                st.success(f"✅ {len(df_new)} produtos carregados!")
                st.rerun()
            else:
                st.warning("⚠️ Nenhum produto encontrado no arquivo.")

    if st.session_state.fisico:
        st.caption(f"💡 {len(st.session_state.fisico)} contagens físicas em memória.")
        if st.button("🔄 Resetar contagem física", use_container_width=True):
            st.session_state.fisico = {}
            st.rerun()

# ── Check data ───────────────────────────────────────────────────────────────
df = st.session_state.df
fisico = st.session_state.fisico

if df is None or df.empty:
    st.info("👆 Faça upload da planilha do BI para começar")
    st.stop()

# ── Stats ────────────────────────────────────────────────────────────────────
total_produtos = len(df)
total_conferidos = sum(1 for _, r in df.iterrows() if r["Chave"] in fisico)
total_divergentes = sum(
    1 for _, r in df.iterrows()
    if r["Chave"] in fisico and fisico[r["Chave"]] != int(r["Qtd_Sistema"])
)
total_ok = total_conferidos - total_divergentes
pct = int(100 * total_conferidos / total_produtos) if total_produtos > 0 else 0

st.markdown(f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-value">{total_conferidos}/{total_produtos}</div>
        <div class="stat-label">Conferidos ({pct}%)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{total_ok}</div>
        <div class="stat-label">✓ Batendo</div>
    </div>
    <div class="stat-card">
        <div class="stat-value red">{total_divergentes}</div>
        <div class="stat-label">✗ Divergentes</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Filter ───────────────────────────────────────────────────────────────────
cats = ["TODOS"] + sorted(df["Categoria"].unique().tolist())
filter_cat = st.radio("Filtro", cats, horizontal=True, label_visibility="collapsed")

tab_mapa, tab_contagem, tab_divergencias = st.tabs(["🗺️ Mapa", "📋 Contagem", "⚠️ Divergências"])

# ── TAB: MAPA ────────────────────────────────────────────────────────────────
with tab_mapa:
    fig = build_treemap(df, fisico, filter_cat)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["toImage", "sendDataToCloud"],
            "displaylogo": False, "scrollZoom": True,
        })
        st.markdown("""
        <div style="text-align:center; font-size:0.65rem; color:#4a5568; margin-top:-10px;">
            🟢 Batendo · 🔴 Divergente · 🟤 Não conferido · Toque p/ zoom
        </div>
        """, unsafe_allow_html=True)

# ── TAB: CONTAGEM ────────────────────────────────────────────────────────────
with tab_contagem:
    st.markdown("""
    <div style="font-size:0.75rem; color:#94a3b8; text-align:center; margin-bottom:8px; line-height:1.5;">
        📱 <b>Contou no galpão? Digite o físico aqui.</b><br>
        <span style="color:#64748b; font-size:0.65rem;">
            "✓ Bate" = confirma rápido · Campo numérico = qtd diferente
        </span>
    </div>
    """, unsafe_allow_html=True)

    filtered_df = df if filter_cat == "TODOS" else df[df["Categoria"] == filter_cat]

    show_filter = st.radio(
        "Mostrar", ["Todos", "Não conferidos", "Divergentes"],
        horizontal=True, label_visibility="collapsed", key="count_filter",
    )
    if show_filter == "Não conferidos":
        filtered_df = filtered_df[~filtered_df["Chave"].isin(fisico.keys())]
    elif show_filter == "Divergentes":
        div_keys = [
            c for c in fisico
            if c in df["Chave"].values
            and fisico[c] != int(df[df["Chave"] == c]["Qtd_Sistema"].iloc[0])
        ]
        filtered_df = filtered_df[filtered_df["Chave"].isin(div_keys)]

    search = st.text_input(
        "Buscar", "", placeholder="🔍 ROUNDUP, BELT, FOX, código...",
        label_visibility="collapsed",
    )
    if search:
        s = search.upper()
        filtered_df = filtered_df[
            filtered_df["Produto"].str.upper().str.contains(s, na=False)
            | filtered_df["Codigo"].str.upper().str.contains(s, na=False)
        ]

    if filtered_df.empty:
        st.info("Nenhum produto neste filtro")
    else:
        changed = False
        for _, row in filtered_df.iterrows():
            chave = row["Chave"]
            prod = str(row["Produto"])
            qtd_sys = int(row["Qtd_Sistema"])
            current_fis = fisico.get(chave, None)
            codigo = str(row.get("Codigo", ""))

            # Status
            if current_fis is None:
                status_icon, card_class = "⬜", ""
            elif current_fis == qtd_sys:
                status_icon, card_class = "🟢", "ok"
            else:
                status_icon, card_class = "🔴", "divergent"

            sn = short_name(prod)
            diff_text = ""
            if current_fis is not None and current_fis != qtd_sys:
                diff = current_fis - qtd_sys
                diff_text = f' · <span class="diff">Diff: {diff:+d}</span>'

            if current_fis is not None:
                bad = " bad" if current_fis != qtd_sys else ""
                fis_display = f'<span class="fis{bad}">Fís: {current_fis}</span>'
            else:
                fis_display = '<span style="color:#4a5568;">Fís: —</span>'

            st.markdown(f"""
            <div class="prod-card {card_class}">
                <div class="prod-name">{status_icon} {sn}</div>
                <div class="prod-info">
                    <span class="sys">Sis: {qtd_sys}</span> · {fis_display}{diff_text}
                    <span style="float:right; color:#2d3748; font-size:0.6rem;">#{codigo}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("✓ Bate", key=f"ok_{chave}", use_container_width=True):
                    st.session_state.fisico[chave] = qtd_sys
                    changed = True
            with c2:
                new_val = st.number_input(
                    "Físico", min_value=0,
                    value=current_fis if current_fis is not None else None,
                    step=1, key=f"inp_{chave}", label_visibility="collapsed",
                    placeholder=f"Contar... (sis: {qtd_sys})",
                )
                if new_val is not None and new_val != current_fis:
                    st.session_state.fisico[chave] = int(new_val)
                    changed = True
            with c3:
                if current_fis is not None:
                    if st.button("✗", key=f"clr_{chave}", use_container_width=True):
                        st.session_state.fisico.pop(chave, None)
                        changed = True

        if changed:
            st.rerun()

    # Bulk actions
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Tudo bate (filtro atual)", use_container_width=True, type="primary"):
            for _, row in filtered_df.iterrows():
                st.session_state.fisico[row["Chave"]] = int(row["Qtd_Sistema"])
            st.rerun()
    with col_b:
        if st.button("🗑️ Limpar contagem", use_container_width=True):
            for _, row in filtered_df.iterrows():
                st.session_state.fisico.pop(row["Chave"], None)
            st.rerun()

# ── TAB: DIVERGÊNCIAS ────────────────────────────────────────────────────────
with tab_divergencias:
    divergentes = []
    for _, row in df.iterrows():
        chave = row["Chave"]
        qtd_sys = int(row["Qtd_Sistema"])
        qtd_fis = fisico.get(chave, None)
        if qtd_fis is not None and qtd_fis != qtd_sys:
            divergentes.append({
                "Produto": short_name(str(row["Produto"])),
                "Codigo": str(row.get("Codigo", "")),
                "Sistema": qtd_sys,
                "Físico": qtd_fis,
                "Diff": qtd_fis - qtd_sys,
                "Categoria": row["Categoria"],
            })

    if not divergentes:
        nao_conf = total_produtos - total_conferidos
        extra = f"<br><span style='font-size:0.7rem; color:#4a5568;'>{nao_conf} ainda não conferidos</span>" if nao_conf > 0 else ""
        st.markdown(f"""
        <div style="text-align:center; padding:40px; color:#00d68f;">
            <div style="font-size:2rem;">✓</div>
            <div style="font-size:0.9rem; margin-top:8px;">Nenhuma divergência</div>
            {extra}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; font-size:0.75rem; color:#ff4757; margin-bottom:8px;">
            ⚠️ {len(divergentes)} divergência{"s" if len(divergentes) > 1 else ""}
        </div>
        """, unsafe_allow_html=True)

        rows_html = ""
        for d in sorted(divergentes, key=lambda x: x["Diff"]):
            sign = "+" if d["Diff"] > 0 else ""
            rows_html += f"""
            <tr>
                <td style="color:#e0e6ed">{d['Produto']}</td>
                <td style="text-align:right; color:#4a90d9;">{d['Sistema']}</td>
                <td style="text-align:right; color:#ff4757;">{d['Físico']}</td>
                <td style="text-align:right; color:#ff4757; font-weight:700;">{sign}{d['Diff']}</td>
            </tr>"""

        st.markdown(f"""
        <table class="div-table">
            <thead><tr>
                <th>Produto</th>
                <th style="text-align:right">Sis.</th>
                <th style="text-align:right">Fís.</th>
                <th style="text-align:right">Diff</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.divider()
        csv = pd.DataFrame(divergentes).to_csv(index=False)
        st.download_button(
            "📥 Exportar divergências (CSV)", csv,
            f"divergencias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv", use_container_width=True,
        )

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; font-size:0.6rem; color:#2d3748; margin-top:1rem; padding:8px;">
    CAMDA Quirinópolis · {datetime.now().strftime('%d/%m/%Y %H:%M')}
    <br>Não entre em pânico 🐬
</div>
""", unsafe_allow_html=True)
