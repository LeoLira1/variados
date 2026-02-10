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
    try:
        row = conn.execute("SELECT data_upload FROM contagens ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return pd.DataFrame()
        df = pd.read_sql_query("SELECT * FROM contagens WHERE data_upload = ?", conn, params=(row[0],))
        return df
    finally:
        conn.close()

# ── Parsing ──────────────────────────────────────────────────────────────────

def classify_product(name: str) -> str:
    n = name.upper()
    categories = [
        ("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"),
        ("INSETICIDAS", "INSETICIDA"), ("NEMATICIDAS", "NEMATICIDA"),
        ("ADUBOS FOLIARES", "ADUBO FOLIAR"), ("ADUBOS QUÍMICOS", "ADUBO Q."),
        ("ÓLEOS", "OLEO")
    ]
    for cat, kw in categories:
        if kw in n:
            return cat
    return "OUTROS"

def short_name(prod: str) -> str:
    prefixes = ["HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "NEMATICIDA ",
                "ADUBO FOLIAR ", "ADUBO Q.", "OLEO VEGETAL ", "OLEO MINERAL "]
    up = prod.upper()
    for p in prefixes:
        if up.startswith(p):
            return prod[len(p):].strip()
    return prod

def parse_annotation(nota: str, qtd_sistema: int) -> tuple:
    if not nota or str(nota).strip().lower() in ["", "nan", "none"]:
        return (qtd_sistema, 0, "")

    text = str(nota).strip().lower()
    # Padrão: "falta 5" ou "passa 2"
    m_falta = re.match(r"falta\s+(\d+)\s*(.*)", text)
    if m_falta:
        val = int(m_falta.group(1))
        return (qtd_sistema - val, -val, m_falta.group(2).strip())

    m_sobra = re.match(r"(pass|sobr)(?:a|ando)\s+(\d+)\s*(.*)", text)
    if m_sobra:
        val = int(m_sobra.group(2))
        return (qtd_sistema + val, val, m_sobra.group(3).strip())

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

    # Coluna E (index 4)
    if len(df.columns) >= 5:
        col_nota = df.columns[4]

    if not col_prod or not col_qtd:
        return (False, "Estrutura de colunas inválida.", None)

    records = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        produto = str(row.get(col_prod, "")).strip()
        if produto.upper() in ["", "NAN", "NONE", "TOTAL", "PRODUTO"]: continue
        
        try:
            qtd_sistema = int(float(row.get(col_qtd, 0)))
            if qtd_sistema <= 0: continue
        except: continue

        nota_raw = str(row.get(col_nota, "")).strip()
        # Limpeza de ruído (valores de custo que caem na col E)
        if re.match(r"^\d+([.,]\d+)?$", nota_raw): nota_raw = ""

        categoria = classify_product(produto)
        qtd_fisica, diferenca, obs = parse_annotation(nota_raw, qtd_sistema)
        status = "ok" if diferenca == 0 else ("falta" if diferenca < 0 else "sobra")

        records.append({
            "data_upload": now, "codigo": str(row.get(col_cod, "")),
            "produto": produto, "categoria": categoria,
            "qtd_sistema": qtd_sistema, "qtd_fisica": qtd_fisica,
            "diferenca": diferenca, "nota": obs, "status": status
        })

    if not records: return (False, "Nenhum dado processado.", None)

    df_res = pd.DataFrame(records)
    conn = get_db()
    df_res.to_sql("contagens", conn, if_exists="append", index=False)
    
    n_div = len(df_res[df_res["status"] != "ok"])
    conn.execute("INSERT INTO historico (data, total_produtos, total_divergentes, total_faltando, total_sobrando) VALUES (?,?,?,?,?)",
                 (now, len(df_res), n_div, len(df_res[df_res["status"] == "falta"]), len(df_res[df_res["status"] == "sobra"])))
    conn.commit()
    conn.close()

    return (True, f"Processado: {len(df_res)} itens.", df_res)

# ── Treemap (FIXED) ──────────────────────────────────────────────────────────

def build_css_treemap(df: pd.DataFrame, filter_cat: str = "TODOS") -> str:
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty: return ""

    # Garantia de tipos numéricos para o cálculo de flex
    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors='coerce').fillna(0)
    df["diferenca"] = pd.to_numeric(df["diferenca"], errors='coerce').fillna(0)
    
    total_val = df["qtd_sistema"].sum()
    if total_val <= 0: total_val = len(df) # fallback para contagem

    categories = df.groupby("categoria")
    cat_html = ""

    # Ordenar categorias por volume
    sorted_cats = df.groupby("categoria")["qtd_sistema"].sum().sort_values(ascending=False).index

    for cat in sorted_cats:
        group = df[df["categoria"] == cat]
        cat_sum = group["qtd_sistema"].sum()
        cat_pct = max((cat_sum / total_val) * 100, 5) if total_val > 0 else 10
        
        prod_html = ""
        # Ordenar produtos dentro da categoria
        for _, r in group.sort_values("qtd_sistema", ascending=False).iterrows():
            q = int(r["qtd_sistema"])
            d = int(r["diferenca"])
            sn = short_name(str(r["produto"]))
            
            # Cálculo de proporção segura
            p_in_cat = max((q / cat_sum) * 100, 2) if cat_sum > 0 else 10
            
            # Cores
            bg = "#00d68f" if d == 0 else ("#ff4757" if d < 0 else "#ffa502")
            txt = "#0a2e1a" if d >= 0 else "#fff"
            info = f"{q}" if d == 0 else (f"Falta {abs(d)}" if d < 0 else f"Sobra +{d}")

            prod_html += f"""
            <div style="flex: {p_in_cat} 1 0; min-width: 55px; min-height: 38px; 
                 background: {bg}; color: {txt}; border-radius: 4px; padding: 3px; 
                 margin: 1px; overflow: hidden; display: flex; flex-direction: column;
                 justify-content: center; border: 1px solid rgba(0,0,0,0.1);" 
                 title="{sn} | Sis: {q} | Diff: {d}">
                <div style="font-size: 0.6rem; font-weight: 700; white-space: nowrap; 
                     text-overflow: ellipsis; overflow: hidden;">{sn}</div>
                <div style="font-size: 0.5rem; opacity: 0.8; font-family: monospace;">{info}</div>
            </div>
            """

        cat_html += f"""
        <div style="flex: {cat_pct} 1 0; min-width: 100px; background: #111827; 
             border-radius: 8px; padding: 6px; border: 1px solid #1e293b; 
             display: flex; flex-direction: column; margin: 2px;">
            <div style="font-size: 0.55rem; color: #64748b; font-weight: 700; 
                 margin-bottom: 4px; font-family: 'JetBrains Mono'; text-transform: uppercase;">
                 {cat}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 1px; flex: 1;">{prod_html}</div>
        </div>
        """

    return f'<div style="display: flex; flex-wrap: wrap; gap: 4px; min-height: 420px; width: 100%;">{cat_html}</div>'

# ── App Logic ────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">MAPA DE CALOR · QUIRINÓPOLIS</div>', unsafe_allow_html=True)

df = st.session_state.df_cache if st.session_state.df_cache is not None else get_latest_data()

with st.expander("📤 Upload da Planilha", expanded=(df.empty)):
    uploaded = st.file_uploader("XLSX", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded and st.session_state.processed_file != uploaded.name:
        with st.spinner("Processando..."):
            ok, msg, res = parse_and_store(uploaded)
            if ok:
                st.session_state.processed_file = uploaded.name
                st.session_state.df_cache = res
                st.rerun()
            else: st.error(msg)

if df.empty:
    st.info("Aguardando upload de dados.")
    st.stop()

# Stats
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Produtos", len(df))
with c2: st.metric("OK", len(df[df["status"]=="ok"]))
with c3: st.metric("Faltas", len(df[df["status"]=="falta"]), delta_color="inverse")
with c4: st.metric("Sobras", len(df[df["status"]=="sobra"]))

# Tabs
tab_m, tab_d, tab_h = st.tabs(["🗺️ Mapa", "⚠️ Divergências", "📊 Histórico"])

with tab_m:
    cats = ["TODOS"] + sorted(df["categoria"].unique().tolist())
    f_cat = st.radio("Filtro", cats, horizontal=True, label_visibility="collapsed")
    st.markdown(build_css_treemap(df, f_cat), unsafe_allow_html=True)

with tab_d:
    df_div = df[df["status"] != "ok"]
    if df_div.empty: st.success("Estoque 100% batendo!")
    else: st.dataframe(df_div[["codigo", "produto", "qtd_sistema", "qtd_fisica", "diferenca", "nota"]], hide_index=True, use_container_width=True)

with tab_h:
    conn = get_db()
    df_hist = pd.read_sql_query("SELECT * FROM historico ORDER BY data DESC LIMIT 10", conn)
    conn.close()
    st.table(df_hist)

st.markdown('<div class="sub-title">CAMDA Quirinópolis · 2026</div>', unsafe_allow_html=True)
