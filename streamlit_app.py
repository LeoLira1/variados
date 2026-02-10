import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import re
import os
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAMDA Estoque",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;500;700;900&display=swap');

    .stApp { background: #0a0f1a; color: #e0e6ed; font-family: 'Outfit', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0.5rem 0.8rem !important; max-width: 100% !important; }

    .main-title {
        font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 1.6rem;
        background: linear-gradient(135deg, #00d68f, #00b887);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin: 0.3rem 0;
    }
    .sub-title {
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
        color: #4a5568; text-align: center; margin-bottom: 0.5rem;
    }

    .stat-row { display: flex; gap: 6px; margin-bottom: 0.5rem; }
    .stat-card {
        flex: 1; background: linear-gradient(135deg, #111827, #1a2332);
        border: 1px solid #1e293b; border-radius: 10px;
        padding: 8px 10px; text-align: center;
    }
    .stat-value {
        font-family: 'JetBrains Mono', monospace; font-size: 1.15rem;
        font-weight: 700; color: #00d68f;
    }
    .stat-value.red { color: #ff4757; }
    .stat-value.amber { color: #ffa502; }
    .stat-label {
        font-size: 0.6rem; color: #64748b;
        text-transform: uppercase; letter-spacing: 1px;
    }

    .stRadio > div {
        flex-direction: row !important; gap: 4px !important;
        flex-wrap: wrap; justify-content: center;
    }
    .stRadio > div > label {
        background: #111827 !important; border: 1px solid #1e293b !important;
        border-radius: 20px !important; padding: 4px 14px !important;
        font-size: 0.75rem !important; color: #94a3b8 !important;
    }

    .div-table {
        width: 100%; border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
    }
    .div-table th {
        background: #111827; color: #64748b; padding: 6px 8px;
        text-align: left; border-bottom: 1px solid #1e293b;
        text-transform: uppercase;
    }
    .div-table td { padding: 5px 8px; border-bottom: 1px solid #0d1420; }

    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camda_estoque.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_upload TEXT NOT NULL,
            codigo TEXT NOT NULL,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            qtd_sistema INTEGER NOT NULL,
            qtd_fisica INTEGER,
            diferenca INTEGER DEFAULT 0,
            nota TEXT DEFAULT '',
            status TEXT DEFAULT 'ok'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            total_produtos INTEGER,
            total_divergentes INTEGER,
            total_faltando INTEGER,
            total_sobrando INTEGER
        )
    """)
    conn.commit()
    return conn


def get_latest_data() -> pd.DataFrame:
    """Get the most recent upload's data."""
    conn = get_db()
    # Get latest upload date
    row = conn.execute("SELECT data_upload FROM contagens ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        conn.close()
        return pd.DataFrame()
    latest_date = row[0]
    df = pd.read_sql_query(
        "SELECT * FROM contagens WHERE data_upload = ?",
        conn, params=(latest_date,)
    )
    conn.close()
    return df


# ── Parsing ──────────────────────────────────────────────────────────────────

def classify_product(name: str) -> str:
    n = name.upper()
    for cat, kw in [("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"),
                     ("INSETICIDAS", "INSETICIDA"), ("NEMATICIDAS", "NEMATICIDA"),
                     ("ADUBOS FOLIARES", "ADUBO FOLIAR"), ("ADUBOS QUÍMICOS", "ADUBO Q."),
                     ("ÓLEOS", "OLEO")]:
        if kw in n:
            return cat
    return "OUTROS"


def short_name(prod: str) -> str:
    """Remove category prefix for cleaner display."""
    prefixes = ["HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "NEMATICIDA ",
                "ADUBO FOLIAR ", "ADUBO Q.", "OLEO VEGETAL ", "OLEO MINERAL "]
    up = prod.upper()
    for p in prefixes:
        if up.startswith(p):
            return prod[len(p):].strip()
    return prod


def parse_annotation(nota: str, qtd_sistema: int) -> tuple:
    """
    Parse annotations like:
      'falta 6 serginho'       → (qtd_sistema - 6, -6, 'serginho')
      'passa 8'                → (qtd_sistema + 8, +8, '')
      'passando 20 investigar' → (qtd_sistema + 20, +20, 'investigar')

    Returns: (qtd_fisica, diferenca, observacao)
    """
    if not nota or str(nota).strip() in ["", "nan", "None"]:
        return (qtd_sistema, 0, "")

    text = str(nota).strip().lower()

    # Pattern: "falta X ..." → physical is LESS than system
    match_falta = re.match(r"falta\s+(\d+)\s*(.*)", text)
    if match_falta:
        falta = int(match_falta.group(1))
        obs = match_falta.group(2).strip()
        return (qtd_sistema - falta, -falta, obs)

    # Pattern: "passa X ..." or "passando X ..." → physical is MORE than system
    match_passa = re.match(r"pass(?:a|ando)\s+(\d+)\s*(.*)", text)
    if match_passa:
        sobra = int(match_passa.group(1))
        obs = match_passa.group(2).strip()
        return (qtd_sistema + sobra, +sobra, obs)

    # Pattern: "sobra X ..." or "sobrando X ..."
    match_sobra = re.match(r"sobr(?:a|ando)\s+(\d+)\s*(.*)", text)
    if match_sobra:
        sobra = int(match_sobra.group(1))
        obs = match_sobra.group(2).strip()
        return (qtd_sistema + sobra, +sobra, obs)

    # Unrecognized annotation — keep as note, no difference
    return (qtd_sistema, 0, str(nota).strip())


def parse_and_store(uploaded_file) -> tuple:
    """Parse Excel, extract annotations, store in SQLite. Returns (success, message, count)."""
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception as e:
        return (False, f"Erro ao ler arquivo: {e}", 0)

    # Find header: row with BOTH 'Produto' AND 'Quantidade'
    header_idx = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().upper() for v in row.tolist()]
        has_prod = any(v == "PRODUTO" for v in vals)
        has_qtd = any("QUANTIDADE" in v for v in vals)
        if has_prod and has_qtd:
            header_idx = i
            break

    if header_idx is None:
        return (False, "Colunas 'Produto' e 'Quantidade' não encontradas.", 0)

    df = df_raw.iloc[header_idx + 1:].copy()
    raw_cols = df_raw.iloc[header_idx].tolist()
    df.columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(raw_cols)]

    # Map columns
    col_prod, col_qtd, col_cod, col_nota = None, None, None, None
    for c in df.columns:
        cu = c.upper()
        if "PRODUTO" in cu and col_prod is None:
            col_prod = c
        elif ("QUANTIDADE" in cu or cu == "QTD") and col_qtd is None:
            col_qtd = c
        elif ("CÓDIGO" in cu or "CODIGO" in cu) and col_cod is None:
            col_cod = c
        elif ("CUSTO" in cu or "OBS" in cu or "NOTA" in cu) and col_nota is None:
            col_nota = c

    # If col_nota wasn't found by name, use the last column (column E = index 4)
    if col_nota is None:
        all_cols = list(df.columns)
        if len(all_cols) >= 5:
            col_nota = all_cols[4]

    if col_prod is None or col_qtd is None:
        return (False, f"Colunas encontradas: {list(df.columns)}", 0)

    # Build clean dataframe
    records = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        produto = str(row.get(col_prod, "")).strip()
        qtd_raw = row.get(col_qtd)
        codigo = str(row.get(col_cod, "")).strip() if col_cod else ""
        nota_raw = str(row.get(col_nota, "")).strip() if col_nota else ""

        # Skip bad rows
        if produto.upper() in ["", "NAN", "NONE", "SUM", "TOTAL", "PRODUTO"]:
            continue
        try:
            qtd_sistema = int(float(qtd_raw))
        except (ValueError, TypeError):
            continue
        if qtd_sistema <= 0:
            continue

        # Clean nota — remove "CUSTO UNITÁRIO" header spillover and numeric-only values
        if nota_raw.upper() in ["NAN", "NONE", "CUSTO UNITÁRIO", ""]:
            nota_raw = ""
        # If nota is just a number (cost value), ignore it
        try:
            float(nota_raw.replace(",", "."))
            nota_raw = ""  # It's a cost value, not an annotation
        except ValueError:
            pass

        categoria = classify_product(produto)
        qtd_fisica, diferenca, observacao = parse_annotation(nota_raw, qtd_sistema)

        status = "ok" if diferenca == 0 else ("falta" if diferenca < 0 else "sobra")

        records.append({
            "data_upload": now,
            "codigo": codigo,
            "produto": produto,
            "categoria": categoria,
            "qtd_sistema": qtd_sistema,
            "qtd_fisica": qtd_fisica,
            "diferenca": diferenca,
            "nota": observacao,
            "status": status,
        })

    if not records:
        return (False, "Nenhum produto válido encontrado.", 0)

    # Store in database
    conn = get_db()
    df_records = pd.DataFrame(records)
    df_records.to_sql("contagens", conn, if_exists="append", index=False)

    # Save summary to historico
    n_div = sum(1 for r in records if r["status"] != "ok")
    n_falta = sum(1 for r in records if r["status"] == "falta")
    n_sobra = sum(1 for r in records if r["status"] == "sobra")
    conn.execute(
        "INSERT INTO historico (data, total_produtos, total_divergentes, total_faltando, total_sobrando) VALUES (?,?,?,?,?)",
        (now, len(records), n_div, n_falta, n_sobra)
    )
    conn.commit()
    conn.close()

    return (True, f"{len(records)} produtos · {n_div} divergências detectadas", len(records))


# ── Treemap ──────────────────────────────────────────────────────────────────

def build_treemap(df: pd.DataFrame, filter_cat: str = "TODOS"):
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty:
        return None

    labels, parents, values, colors, custom_text = [], [], [], [], []

    labels.append("ESTOQUE CAMDA")
    parents.append("")
    values.append(0)
    colors.append("#1a2332")
    custom_text.append("")

    for cat in sorted(df["categoria"].unique()):
        labels.append(cat)
        parents.append("ESTOQUE CAMDA")
        values.append(0)
        colors.append("#1a2332")
        custom_text.append("")

    for _, row in df.iterrows():
        qtd_sys = int(row["qtd_sistema"])
        diff = int(row["diferenca"])
        nota = str(row.get("nota", ""))

        sn = short_name(str(row["produto"]))
        if len(sn) > 24:
            sn = sn[:22] + "…"

        labels.append(sn)
        parents.append(row["categoria"])
        values.append(max(qtd_sys, 1))

        if diff == 0:
            colors.append("#00d68f")  # Green — OK
            custom_text.append(f"✓ {qtd_sys}")
        elif diff < 0:
            colors.append("#ff4757")  # Red — missing
            nota_txt = f" · {nota}" if nota else ""
            custom_text.append(f"Falta {abs(diff)} (Sis:{qtd_sys} Fís:{qtd_sys+diff}){nota_txt}")
        else:
            colors.append("#ffa502")  # Amber — excess
            nota_txt = f" · {nota}" if nota else ""
            custom_text.append(f"Sobra +{diff} (Sis:{qtd_sys} Fís:{qtd_sys+diff}){nota_txt}")

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
        margin=dict(t=5, l=2, r=2, b=2), height=550,
        font=dict(family="Outfit", color="#e0e6ed"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">MAPA DE CALOR · QUIRINÓPOLIS</div>', unsafe_allow_html=True)

# ── Upload ───────────────────────────────────────────────────────────────────
df = get_latest_data()

with st.expander("📤 Upload da Planilha Conferida", expanded=df.empty):
    st.markdown("""
    <div style="font-size:0.7rem; color:#64748b; margin-bottom:6px; line-height:1.4;">
        Suba a planilha do BI <b>com suas anotações</b> na coluna E.<br>
        <span style="color:#4a5568;">
            Reconhece: "falta 6 serginho" · "passa 8" · "passando 20 investigar"
        </span>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("XLSX", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded is not None:
        with st.spinner("🔄 Lendo planilha e detectando divergências..."):
            ok, msg, count = parse_and_store(uploaded)
        if ok:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ {msg}")

if df.empty:
    st.info("👆 Faça upload da planilha conferida para gerar o mapa")
    st.stop()

# ── Stats ────────────────────────────────────────────────────────────────────
total = len(df)
n_ok = len(df[df["status"] == "ok"])
n_falta = len(df[df["status"] == "falta"])
n_sobra = len(df[df["status"] == "sobra"])
n_div = n_falta + n_sobra

# Upload date
data_upload = df["data_upload"].iloc[0] if "data_upload" in df.columns else ""

st.markdown(f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Produtos</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{n_ok}</div>
        <div class="stat-label">✓ OK</div>
    </div>
    <div class="stat-card">
        <div class="stat-value red">{n_falta}</div>
        <div class="stat-label">Faltando</div>
    </div>
    <div class="stat-card">
        <div class="stat-value amber">{n_sobra}</div>
        <div class="stat-label">Sobrando</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Filter ───────────────────────────────────────────────────────────────────
cats = ["TODOS"] + sorted(df["categoria"].unique().tolist())
filter_cat = st.radio("Filtro", cats, horizontal=True, label_visibility="collapsed")

tab_mapa, tab_divergencias, tab_historico = st.tabs(["🗺️ Mapa", "⚠️ Divergências", "📊 Histórico"])

# ── TAB: MAPA ────────────────────────────────────────────────────────────────
with tab_mapa:
    fig = build_treemap(df, filter_cat)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["toImage", "sendDataToCloud"],
            "displaylogo": False, "scrollZoom": True,
        })
        st.markdown("""
        <div style="text-align:center; font-size:0.65rem; color:#4a5568; margin-top:-10px;">
            🟢 OK · 🔴 Faltando · 🟡 Sobrando · Toque p/ zoom
        </div>
        """, unsafe_allow_html=True)

# ── TAB: DIVERGÊNCIAS ────────────────────────────────────────────────────────
with tab_divergencias:
    df_div = df[df["status"] != "ok"].copy()

    if filter_cat != "TODOS":
        df_div = df_div[df_div["categoria"] == filter_cat]

    if df_div.empty:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#00d68f;">
            <div style="font-size:2rem;">✓</div>
            <div style="font-size:0.9rem; margin-top:8px;">Tudo batendo!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; font-size:0.75rem; color:#ff4757; margin-bottom:8px;">
            ⚠️ {len(df_div)} divergência{"s" if len(df_div) > 1 else ""}
        </div>
        """, unsafe_allow_html=True)

        rows_html = ""
        for _, d in df_div.sort_values("diferenca").iterrows():
            diff = int(d["diferenca"])
            sign = "+" if diff > 0 else ""
            color = "#ff4757" if diff < 0 else "#ffa502"
            nota = str(d.get("nota", ""))
            nota_html = f'<br><span style="color:#4a5568; font-size:0.6rem;">{nota}</span>' if nota and nota not in ["", "nan"] else ""

            rows_html += f"""
            <tr>
                <td style="color:#e0e6ed">{short_name(str(d['produto']))}{nota_html}</td>
                <td style="text-align:right; color:#4a90d9;">{int(d['qtd_sistema'])}</td>
                <td style="text-align:right; color:{color};">{int(d['qtd_fisica'])}</td>
                <td style="text-align:right; color:{color}; font-weight:700;">{sign}{diff}</td>
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
        export_data = df_div[["codigo", "produto", "categoria", "qtd_sistema", "qtd_fisica", "diferenca", "nota"]].copy()
        csv = export_data.to_csv(index=False)
        st.download_button(
            "📥 Exportar divergências", csv,
            f"divergencias_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv", use_container_width=True,
        )

# ── TAB: HISTÓRICO ───────────────────────────────────────────────────────────
with tab_historico:
    conn = get_db()
    df_hist = pd.read_sql_query(
        "SELECT * FROM historico ORDER BY data DESC LIMIT 30", conn
    )
    conn.close()

    if df_hist.empty:
        st.info("Histórico vazio — suba planilhas para começar a rastrear.")
    else:
        st.markdown("""
        <div style="font-size:0.75rem; color:#94a3b8; text-align:center; margin-bottom:8px;">
            📊 Evolução das contagens
        </div>
        """, unsafe_allow_html=True)

        if len(df_hist) > 1:
            fig_hist = go.Figure()
            dates = df_hist["data"].tolist()[::-1]
            fig_hist.add_trace(go.Scatter(
                x=dates, y=df_hist["total_faltando"].tolist()[::-1],
                name="Faltando", line=dict(color="#ff4757", width=2),
                fill="tozeroy", fillcolor="rgba(255,71,87,0.1)",
            ))
            fig_hist.add_trace(go.Scatter(
                x=dates, y=df_hist["total_sobrando"].tolist()[::-1],
                name="Sobrando", line=dict(color="#ffa502", width=2),
                fill="tozeroy", fillcolor="rgba(255,165,2,0.1)",
            ))
            fig_hist.update_layout(
                paper_bgcolor="#0a0f1a", plot_bgcolor="#0a0f1a",
                margin=dict(t=10, l=30, r=10, b=30), height=250,
                font=dict(family="JetBrains Mono", size=10, color="#64748b"),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center",
                           font=dict(size=10)),
                xaxis=dict(gridcolor="#1e293b", showgrid=False),
                yaxis=dict(gridcolor="#1e293b", title="Qtd"),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # Table
        rows_html = ""
        for _, h in df_hist.iterrows():
            d = str(h["data"])[:16]
            rows_html += f"""
            <tr>
                <td style="color:#94a3b8">{d}</td>
                <td style="text-align:right; color:#e0e6ed">{int(h['total_produtos'])}</td>
                <td style="text-align:right; color:#ff4757">{int(h['total_faltando'])}</td>
                <td style="text-align:right; color:#ffa502">{int(h['total_sobrando'])}</td>
            </tr>"""

        st.markdown(f"""
        <table class="div-table">
            <thead><tr>
                <th>Data</th>
                <th style="text-align:right">Prod.</th>
                <th style="text-align:right">Falta</th>
                <th style="text-align:right">Sobra</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        # Admin: clear DB
        st.divider()
        if st.button("🗑️ Limpar banco de dados", use_container_width=True):
            conn = get_db()
            conn.execute("DELETE FROM contagens")
            conn.execute("DELETE FROM historico")
            conn.commit()
            conn.close()
            st.success("Banco limpo")
            st.rerun()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; font-size:0.6rem; color:#2d3748; margin-top:1rem; padding:8px;">
    CAMDA Quirinópolis · {data_upload[:16] if data_upload else ''} · v2
    <br>Não entre em pânico 🐬
</div>
""", unsafe_allow_html=True)
