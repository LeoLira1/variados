import streamlit as st
import pandas as pd
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

# ── Session State ────────────────────────────────────────────────────────────
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
if "df_cache" not in st.session_state:
    st.session_state.df_cache = None

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
    conn = get_db()
    row = conn.execute("SELECT data_upload FROM contagens ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        conn.close()
        return pd.DataFrame()
    df = pd.read_sql_query(
        "SELECT * FROM contagens WHERE data_upload = ?", conn, params=(row[0],)
    )
    conn.close()
    return df

# ── Parsing ──────────────────────────────────────────────────────────────────

def classify_product(name: str) -> str:
    n = str(name).upper()
    for cat, kw in [("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"),
                     ("INSETICIDAS", "INSETICIDA"), ("NEMATICIDAS", "NEMATICIDA"),
                     ("ADUBOS FOLIARES", "ADUBO FOLIAR"), ("ADUBOS QUÍMICOS", "ADUBO Q."),
                     ("ÓLEOS", "OLEO")]:
        if kw in n:
            return cat
    return "OUTROS"

def short_name(prod: str) -> str:
    prefixes = ["HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "NEMATICIDA ",
                "ADUBO FOLIAR ", "ADUBO Q.", "OLEO VEGETAL ", "OLEO MINERAL "]
    up = str(prod).upper()
    for p in prefixes:
        if up.startswith(p):
            return str(prod)[len(p):].strip()
    return str(prod)

def parse_annotation(nota: str, qtd_sistema: int) -> tuple:
    if not nota or str(nota).strip().lower() in ["", "nan", "none"]:
        return (qtd_sistema, 0, "")

    text = str(nota).strip().lower()

    m = re.match(r"falta\s+(\d+)\s*(.*)", text)
    if m:
        falta = int(m.group(1))
        return (qtd_sistema - falta, -falta, m.group(2).strip())

    m = re.match(r"(pass|sobr)(?:a|ando)\s+(\d+)\s*(.*)", text)
    if m:
        sobra = int(m.group(2))
        return (qtd_sistema + sobra, +sobra, m.group(3).strip())

    return (qtd_sistema, 0, str(nota).strip())

def parse_and_store(uploaded_file) -> tuple:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception as e:
        return (False, f"Erro ao ler arquivo: {e}", None)

    header_idx = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().upper() for v in row.tolist()]
        if any(v == "PRODUTO" for v in vals) and any("QUANTIDADE" in v for v in vals):
            header_idx = i
            break

    if header_idx is None:
        return (False, "Colunas 'Produto' e 'Quantidade' não encontradas.", None)

    df = df_raw.iloc[header_idx + 1:].copy()
    raw_cols = df_raw.iloc[header_idx].tolist()
    df.columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(raw_cols)]

    col_prod, col_qtd, col_cod, col_nota = None, None, None, None
    for c in df.columns:
        cu = c.upper()
        if "PRODUTO" in cu and col_prod is None: col_prod = c
        elif ("QUANTIDADE" in cu or cu == "QTD") and col_qtd is None: col_qtd = c
        elif ("CÓDIGO" in cu or "CODIGO" in cu) and col_cod is None: col_cod = c

    if len(df.columns) >= 5:
        col_nota = df.columns[4]

    if col_prod is None or col_qtd is None:
        return (False, "Faltou identificar as colunas obrigatórias.", None)

    records = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        produto = str(row.get(col_prod, "")).strip()
        if produto.upper() in ["", "NAN", "NONE", "TOTAL", "PRODUTO"]: continue
        
        try:
            # VACINA CONTRA O VALUEERROR
            raw_val = row.get(col_qtd)
            if pd.isna(raw_val): continue
            qtd_sistema = int(float(raw_val))
            if qtd_sistema <= 0: continue
        except: continue

        nota_raw = str(row.get(col_nota, "")).strip()
        if re.match(r"^\d+([.,]\d+)?$", nota_raw): nota_raw = ""

        categoria = classify_product(produto)
        qtd_fisica, diferenca, observacao = parse_annotation(nota_raw, qtd_sistema)
        status = "ok" if diferenca == 0 else ("falta" if diferenca < 0 else "sobra")

        records.append({
            "data_upload": now, "codigo": str(row.get(col_cod, "")),
            "produto": produto, "categoria": categoria,
            "qtd_sistema": qtd_sistema, "qtd_fisica": qtd_fisica,
            "diferenca": diferenca, "nota": observacao, "status": status,
        })

    if not records: return (False, "Nenhum dado válido.", None)

    df_records = pd.DataFrame(records)
    conn = get_db()
    df_records.to_sql("contagens", conn, if_exists="append", index=False)
    
    n_div = sum(1 for r in records if r["status"] != "ok")
    conn.execute("INSERT INTO historico (data, total_produtos, total_divergentes, total_faltando, total_sobrando) VALUES (?,?,?,?,?)",
                 (now, len(records), n_div, sum(1 for r in records if r["status"] == "falta"), sum(1 for r in records if r["status"] == "sobra")))
    conn.commit()
    conn.close()

    return (True, f"{len(records)} produtos processados", df_records)

# ── Treemap (Visualização Grid) ──────────────────────────────────────────────

def build_css_treemap(df: pd.DataFrame, filter_cat: str = "TODOS") -> str:
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty: return ""

    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors='coerce').fillna(0)
    
    # Agrupa por categoria
    categories = {}
    for _, row in df.iterrows():
        cat = row["categoria"]
        if cat not in categories: categories[cat] = []
        categories[cat].append(row)

    # Ordena categorias por volume total
    sorted_cats = sorted(categories.keys(), key=lambda c: sum(int(r["qtd_sistema"]) for r in categories[c]), reverse=True)
    blocks_html = ""

    for cat in sorted_cats:
        rows = categories[cat]
        
        products_html = ""
        # Ordena produtos por quantidade (opcional, apenas para manter organizacao visual)
        for r in sorted(rows, key=lambda x: int(x["qtd_sistema"]), reverse=True):
            qs, diff = int(r["qtd_sistema"]), int(r["diferenca"])
            
            # Cores
            bg = "#00d68f" if diff == 0 else ("#ff4757" if diff < 0 else "#ffa502")
            txt = "#0a2e1a" if diff >= 0 else "#fff"
            info = f"{qs}" if diff == 0 else (f"Faltam {abs(diff)}" if diff < 0 else f"Sobram {diff}")

            # CARD FIXO: width 110px, height 60px
            products_html += f"""
            <div style="width: 110px; height: 60px; background: {bg}; color: {txt}; 
                 border-radius: 4px; padding: 4px; margin: 2px; 
                 display: flex; flex-direction: column; justify-content: center; align-items: center;
                 overflow: hidden; border: 1px solid rgba(0,0,0,0.1);" title="{r['produto']} - Qtd: {qs}">
                <div style="font-size: 0.55rem; font-weight: 700; text-align: center; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{short_name(r['produto'])}</div>
                <div style="font-size: 0.65rem; opacity: 0.9; font-family: monospace; font-weight: bold; margin-top: 2px;">{info}</div>
            </div>"""

        # Container da Categoria
        blocks_html += f"""
        <div style="width: 100%; background: #111827; border-radius: 8px; padding: 8px; 
             margin-bottom: 8px; border: 1px solid #1e293b; display: flex; flex-direction: column;">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">{cat}</div>
            <div style="display: flex; flex-wrap: wrap; gap: 2px;">{products_html}</div>
        </div>"""

    return f'<div style="display: flex; flex-direction: column; min-height: 450px;">{blocks_html}</div>'

# ── MAIN APP ─────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">MAPA DE CALOR · QUIRINÓPOLIS</div>', unsafe_allow_html=True)

df = st.session_state.df_cache if st.session_state.df_cache is not None else get_latest_data()

with st.expander("📤 Upload da Planilha", expanded=df.empty):
    uploaded = st.file_uploader("XLSX", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded and st.session_state.processed_file != uploaded.name:
        ok, msg, res = parse_and_store(uploaded)
        if ok:
            st.session_state.processed_file = uploaded.name
            st.session_state.df_cache = res
            st.rerun()
        else: st.error(msg)

if not df.empty:
    n_falta, n_sobra = len(df[df["status"]=="falta"]), len(df[df["status"]=="sobra"])
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card"><div class="stat-value">{len(df)}</div><div class="stat-label">Produtos</div></div>
        <div class="stat-card"><div class="stat-value">{len(df[df["status"]=="ok"])}</div><div class="stat-label">OK</div></div>
        <div class="stat-card"><div class="stat-value red">{n_falta}</div><div class="stat-label">Faltas</div></div>
        <div class="stat-card"><div class="stat-value amber">{n_sobra}</div><div class="stat-label">Sobras</div></div>
    </div>
    """, unsafe_allow_html=True)

    cats = ["TODOS"] + sorted(df["categoria"].unique().tolist())
    f_cat = st.radio("Filtro", cats, horizontal=True, label_visibility="collapsed")
    
    t1, t2, t3 = st.tabs(["🗺️ Mapa", "⚠️ Divergências", "📊 Histórico"])
    with t1: st.markdown(build_css_treemap(df, f_cat), unsafe_allow_html=True)
    with t2: st.dataframe(df[df["status"]!="ok"][["produto", "qtd_sistema", "qtd_fisica", "diferenca", "nota"]], hide_index=True, use_container_width=True)
    with t3: 
        conn = get_db()
        st.table(pd.read_sql_query("SELECT * FROM historico ORDER BY data DESC LIMIT 10", conn))
        conn.close()
