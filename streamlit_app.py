import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAMDA Estoque",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS for mobile-optimized dark theme ───────────────────────────────
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
        letter-spacing: -0.5px;
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

    /* Product card for counting */
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
    .prod-card.ok {
        border-color: #00d68f33;
    }
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

    /* Filter chips */
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

    .stFileUploader label { font-size: 0.75rem !important; }

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
        letter-spacing: 0.5px;
    }
    .div-table td {
        padding: 5px 8px;
        border-bottom: 1px solid #0d1420;
        color: #ff4757;
    }

    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0a0f1a; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Data paths ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_FILE = os.path.join(DATA_DIR, "estoque_sistema.csv")
FISICO_FILE = os.path.join(DATA_DIR, "contagem_fisica.json")


def classify_product(name: str) -> str:
    n = name.upper()
    if "HERBICIDA" in n:
        return "HERBICIDAS"
    elif "FUNGICIDA" in n:
        return "FUNGICIDAS"
    elif "INSETICIDA" in n:
        return "INSETICIDAS"
    elif "NEMATICIDA" in n:
        return "NEMATICIDAS"
    else:
        return "OUTROS"


def parse_excel(uploaded_file) -> pd.DataFrame:
    df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)

    header_idx = None
    for i, row in df_raw.iterrows():
        vals = row.astype(str).str.upper().tolist()
        if "PRODUTO" in vals:
            header_idx = i
            break

    if header_idx is None:
        st.error("❌ Formato não reconhecido. A planilha precisa ter a coluna 'Produto'.")
        return pd.DataFrame()

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = df_raw.iloc[header_idx].tolist()

    col_map = {}
    for c in df.columns:
        cu = str(c).upper().strip()
        if "PRODUTO" in cu:
            col_map["Produto"] = c
        elif "QUANTIDADE" in cu or "QTD" in cu:
            col_map["Qtd_Sistema"] = c
        elif "CÓDIGO" in cu or "CODIGO" in cu or "CÓD" in cu:
            col_map["Codigo"] = c

    if "Produto" not in col_map or "Qtd_Sistema" not in col_map:
        st.error("❌ Colunas 'Produto' e 'Quantidade' não encontradas.")
        return pd.DataFrame()

    result = pd.DataFrame()
    result["Produto"] = df[col_map["Produto"]].astype(str).str.strip()
    result["Qtd_Sistema"] = pd.to_numeric(df[col_map["Qtd_Sistema"]], errors="coerce")

    if "Codigo" in col_map:
        result["Codigo"] = df[col_map["Codigo"]].astype(str).str.strip()
    else:
        result["Codigo"] = ""

    result = result.dropna(subset=["Produto", "Qtd_Sistema"])
    result = result[~result["Produto"].str.upper().isin(["SUM", "TOTAL", "", "NAN", "NONE"])]
    result = result[result["Qtd_Sistema"] > 0]
    result["Qtd_Sistema"] = result["Qtd_Sistema"].astype(int)
    result["Categoria"] = result["Produto"].apply(classify_product)

    # Stable key by product code (survives name changes)
    result["Chave"] = result.apply(
        lambda r: r["Codigo"] if r["Codigo"] not in ["", "nan", "None"] else r["Produto"],
        axis=1,
    )

    return result.reset_index(drop=True)


def load_fisico() -> dict:
    if os.path.exists(FISICO_FILE):
        with open(FISICO_FILE, "r") as f:
            return json.load(f)
    return {}


def save_fisico(data: dict):
    with open(FISICO_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def short_name(prod: str) -> str:
    parts = prod.split(" ", 1)
    return parts[-1] if len(parts) > 1 else prod


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

    for cat in df["Categoria"].unique():
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
            custom_text.append(f"Sis: {qtd_sys} · não conferido")
        elif qtd_fis == qtd_sys:
            colors.append("#00d68f")
            custom_text.append(f"✓ {qtd_sys}")
        else:
            diff = qtd_fis - qtd_sys
            colors.append("#ff4757")
            custom_text.append(f"Sis: {qtd_sys} | Fís: {qtd_fis} ({diff:+d})")

    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        marker=dict(colors=colors, line=dict(width=1.5, color="#0a0f1a")),
        textinfo="label+text", text=custom_text,
        textfont=dict(family="JetBrains Mono, monospace", size=11),
        hovertemplate="<b>%{label}</b><br>%{text}<br>Peso: %{value}<extra></extra>",
        pathbar=dict(visible=True, textfont=dict(family="Outfit", size=11, color="#64748b"), thickness=20, edgeshape=">"),
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

# ── Load / Upload ────────────────────────────────────────────────────────────
df = pd.DataFrame()
if os.path.exists(STOCK_FILE):
    df = pd.read_csv(STOCK_FILE)

with st.expander("📤 Atualizar Planilha do BI", expanded=not os.path.exists(STOCK_FILE)):
    uploaded = st.file_uploader("Arraste o XLSX do BI", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded:
        df_new = parse_excel(uploaded)
        if not df_new.empty:
            df_new.to_csv(STOCK_FILE, index=False)
            st.success(f"✅ {len(df_new)} produtos carregados · {datetime.now().strftime('%d/%m %H:%M')}")
            st.rerun()
    if os.path.exists(FISICO_FILE):
        st.caption("💡 Contagem física anterior é mantida ao subir planilha nova.")
        if st.button("🔄 Resetar contagem física", use_container_width=True):
            os.remove(FISICO_FILE)
            st.success("Contagem zerada")
            st.rerun()

if df.empty:
    st.info("👆 Faça upload da planilha do BI para começar")
    st.stop()

# Ensure Chave column
if "Chave" not in df.columns:
    df["Chave"] = df.apply(
        lambda r: str(r.get("Codigo", "")) if str(r.get("Codigo", "")) not in ["", "nan", "None"] else str(r["Produto"]),
        axis=1,
    )

fisico = load_fisico()

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
            Botão "✓ Bate" → confirma rápido. Ou digite a qtd real.
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
        div_keys = [c for c in fisico if c in df["Chave"].values and fisico[c] != int(df[df["Chave"] == c]["Qtd_Sistema"].iloc[0])]
        filtered_df = filtered_df[filtered_df["Chave"].isin(div_keys)]

    search = st.text_input("Buscar", "", placeholder="🔍 ROUNDUP, BELT, FOX, código...", label_visibility="collapsed")
    if search:
        s = search.upper()
        filtered_df = filtered_df[
            filtered_df["Produto"].str.contains(s, case=False, na=False)
            | filtered_df["Codigo"].str.contains(s, case=False, na=False)
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
                    fisico[chave] = qtd_sys
                    changed = True
            with c2:
                new_val = st.number_input(
                    "Físico", min_value=0,
                    value=current_fis if current_fis is not None else None,
                    step=1, key=f"inp_{chave}", label_visibility="collapsed",
                    placeholder=f"Contar... (sis: {qtd_sys})",
                )
                if new_val is not None and new_val != current_fis:
                    fisico[chave] = int(new_val)
                    changed = True
            with c3:
                if current_fis is not None:
                    if st.button("✗", key=f"clr_{chave}", use_container_width=True):
                        fisico.pop(chave, None)
                        changed = True

        if changed:
            save_fisico(fisico)
            st.rerun()

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Tudo bate (filtro atual)", use_container_width=True, type="primary"):
            for _, row in filtered_df.iterrows():
                fisico[row["Chave"]] = int(row["Qtd_Sistema"])
            save_fisico(fisico)
            st.rerun()
    with col_b:
        if st.button("🗑️ Limpar contagem", use_container_width=True):
            for _, row in filtered_df.iterrows():
                fisico.pop(row["Chave"], None)
            save_fisico(fisico)
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
        extra = f"<br><span style='font-size:0.7rem; color:#4a5568;'>{nao_conf} produtos ainda não conferidos</span>" if nao_conf > 0 else ""
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
                <td style="text-align:right; font-weight:700;">{sign}{d['Diff']}</td>
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
