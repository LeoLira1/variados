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
    .stRadio > div { flex-direction: row !important; gap: 4px !important; justify-content: center; }
</style>
""", unsafe_allow_html=True)

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = "camda_estoque.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS contagens (id INTEGER PRIMARY KEY AUTOINCREMENT, data_upload TEXT, codigo TEXT, produto TEXT, categoria TEXT, qtd_sistema INTEGER, qtd_fisica INTEGER, diferenca INTEGER, nota TEXT, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, total_produtos INTEGER, total_divergentes INTEGER, total_faltando INTEGER, total_sobrando INTEGER)")
    conn.commit()
    return conn

def get_latest_data():
    conn = get_db()
    row = conn.execute("SELECT data_upload FROM contagens ORDER BY id DESC LIMIT 1").fetchone()
    if not row: return pd.DataFrame()
    df = pd.read_sql_query("SELECT * FROM contagens WHERE data_upload = ?", conn, params=(row[0],))
    conn.close()
    return df

# ── Funções de Apoio ──────────────────────────────────────────────────────────
def classify_product(name):
    n = str(name).upper()
    for cat, kw in [("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"), ("INSETICIDAS", "INSETICIDA"), ("ADUBOS", "ADUBO"), ("ÓLEOS", "OLEO")]:
        if kw in n: return cat
    return "OUTROS"

def short_name(prod):
    p_list = ["HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "ADUBO ", "OLEO "]
    for p in p_list:
        if str(prod).upper().startswith(p): return str(prod)[len(p):].strip()
    return str(prod)

def parse_annotation(nota, qtd_sistema):
    if not nota or str(nota).lower() in ["nan", "none", ""]: return (qtd_sistema, 0, "")
    text = str(nota).lower()
    m_f = re.search(r"falta\s+(\d+)", text)
    if m_f:
        v = int(m_f.group(1))
        return (qtd_sistema - v, -v, text)
    m_s = re.search(r"(pass|sobr)\w*\s+(\d+)", text)
    if m_s:
        v = int(m_s.group(2))
        return (qtd_sistema + v, v, text)
    return (qtd_sistema, 0, text)

# ── Treemap ──────────────────────────────────────────────────────────────────
def build_css_treemap(df, filter_cat="TODOS"):
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty: return ""

    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors='coerce').fillna(0)
    total_geral = df["qtd_sistema"].sum() or len(df)
    
    cat_blocks = ""
    for cat in df["categoria"].unique():
        sub = df[df["categoria"] == cat]
        cat_sum = sub["qtd_sistema"].sum() or 1
        cat_w = max((cat_sum / total_geral) * 100, 5)
        
        prod_items = ""
        for _, r in sub.sort_values("qtd_sistema", ascending=False).iterrows():
            q, d = int(r["qtd_sistema"]), int(r["diferenca"])
            p_w = max((q / cat_sum) * 100, 2)
            bg = "#00d68f" if d == 0 else ("#ff4757" if d < 0 else "#ffa502")
            color = "#0a2e1a" if d >= 0 else "#fff"
            
            prod_items += f"""
            <div style="flex: {p_w} 1 0; min-width: 65px; min-height: 45px; background: {bg}; 
                 margin: 1px; border-radius: 4px; padding: 4px; display: flex; flex-direction: column; 
                 justify-content: center; overflow: hidden; border: 1px solid rgba(0,0,0,0.1);"
                 title="{r['produto']} | Qtd: {q}">
                <div style="font-size: 0.6rem; font-weight: 700; color: {color}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{short_name(r['produto'])}</div>
                <div style="font-size: 0.5rem; color: {color}; opacity: 0.8;">{q} {f'({d:+})' if d != 0 else ''}</div>
            </div>"""
            
        cat_blocks += f"""
        <div style="flex: {cat_w} 1 0; min-width: 160px; background: #111827; border: 1px solid #1e293b; 
             border-radius: 8px; padding: 8px; margin: 3px; display: flex; flex-direction: column;">
            <div style="font-size: 0.6rem; color: #64748b; font-weight: 700; margin-bottom: 5px;">{cat}</div>
            <div style="display: flex; flex-wrap: wrap; flex: 1;">{prod_items}</div>
        </div>"""
    
    return f'<div style="display: flex; flex-wrap: wrap; width: 100%; min-height: 500px;">{cat_blocks}</div>'

# ── App Main ─────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)

if st.session_state.df_cache is None:
    st.session_state.df_cache = get_latest_data()

df = st.session_state.df_cache

with st.expander("📤 UPLOAD PLANILHA", expanded=df.empty):
    file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
    if file and st.session_state.processed_file != file.name:
        try:
            df_raw = pd.read_excel(file)
            records = []
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            for _, row in df_raw.iterrows():
                try:
                    # CORREÇÃO DO VALUERROR: Usando conversão segura
                    qtd_val = row.iloc[3]
                    qtd = int(float(qtd_val)) if pd.notnull(qtd_val) else 0
                    prod = str(row.iloc[1])
                    if prod.upper() in ["NAN", "PRODUTO", "TOTAL"]: continue
                    
                    nota = str(row.iloc[4]) if len(row) > 4 else ""
                    fis, diff, obs = parse_annotation(nota, qtd)
                    records.append({
                        "data_upload": now, "produto": prod, "categoria": classify_product(prod),
                        "qtd_sistema": qtd, "qtd_fisica": fis, "diferenca": diff, "status": "ok" if diff==0 else "erro"
                    })
                except: continue # Pula linhas com erro de formato

            if records:
                new_df = pd.DataFrame(records)
                new_df.to_sql("contagens", get_db(), if_exists="append", index=False)
                st.session_state.df_cache = new_df
                st.session_state.processed_file = file.name
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

if not df.empty:
    cats = ["TODOS"] + sorted(df["categoria"].unique().tolist())
    sel = st.radio("", cats, horizontal=True)
    st.markdown(build_css_treemap(df, sel), unsafe_allow_html=True)
