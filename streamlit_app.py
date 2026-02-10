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

# ── CSS Geral do Dashboard ───────────────────────────────────────────────────
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

    /* Estilo dos Botões de Filtro */
    .stRadio > div {
        flex-direction: row !important; gap: 4px !important;
        flex-wrap: wrap; justify-content: center;
    }
    .stRadio div[role="radiogroup"] > label {
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
    }
    .div-table td { padding: 5px 8px; border-bottom: 1px solid #0d1420; }
</style>
""", unsafe_allow_html=True)

# ── Database & Funções de Apoio ──────────────────────────────────────────────
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

def classify_product(name):
    n = name.upper()
    for cat, kw in [("HERBICIDAS", "HERBICIDA"), ("FUNGICIDAS", "FUNGICIDA"), ("INSETICIDAS", "INSETICIDA"), ("ADUBOS", "ADUBO"), ("ÓLEOS", "OLEO")]:
        if kw in n: return cat
    return "OUTROS"

def short_name(prod):
    for p in ["HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "ADUBO ", "OLEO "]:
        if prod.upper().startswith(p): return prod[len(p):].strip()
    return prod

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

# ── FUNÇÃO DO MAPA (Treemap) ─────────────────────────────────────────────────
def build_css_treemap(df, filter_cat="TODOS"):
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty: return ""

    # Garantir números
    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors='coerce').fillna(0)
    df["diferenca"] = pd.to_numeric(df["diferenca"], errors='coerce').fillna(0)
    
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
            <div style="flex: {p_w} 1 0; min-width: 60px; min-height: 45px; background: {bg}; 
                 margin: 1px; border-radius: 4px; padding: 4px; display: flex; flex-direction: column; 
                 justify-content: center; overflow: hidden; border: 1px solid rgba(0,0,0,0.1);"
                 title="{r['produto']} | Sis: {q} | Diff: {d}">
                <div style="font-size: 0.6rem; font-weight: 700; color: {color}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{short_name(r['produto'])}</div>
                <div style="font-size: 0.5rem; color: {color}; opacity: 0.8; font-family: monospace;">{q} {f'({d:+})' if d != 0 else ''}</div>
            </div>
            """
            
        cat_blocks += f"""
        <div style="flex: {cat_w} 1 0; min-width: 150px; background: #111827; border: 1px solid #1e293b; 
             border-radius: 8px; padding: 8px; margin: 3px; display: flex; flex-direction: column;">
            <div style="font-size: 0.6rem; color: #64748b; font-weight: 700; margin-bottom: 5px; text-transform: uppercase;">{cat}</div>
            <div style="display: flex; flex-wrap: wrap; flex: 1;">{prod_items}</div>
        </div>
        """
    
    return f'<div style="display: flex; flex-wrap: wrap; width: 100%; min-height: 500px;">{cat_blocks}</div>'

# ── App Main ─────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">QUIRINÓPOLIS-GO · {datetime.now().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

# Lógica de Dados
if st.session_state.df_cache is None:
    st.session_state.df_cache = get_latest_data()

df = st.session_state.df_cache

# Sidebar/Upload
with st.expander("📤 ATUALIZAR ESTOQUE (XLSX)", expanded=df.empty):
    file = st.file_uploader("Arraste a planilha aqui", type=["xlsx"])
    if file and st.session_state.processed_file != file.name:
        df_raw = pd.read_excel(file)
        # Lógica simplificada de parse para o exemplo
        records = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for _, row in df_raw.iterrows():
            prod = str(row.iloc[1]) # Assume coluna B como produto
            qtd = int(row.iloc[3]) # Assume coluna D como quantidade
            nota = str(row.iloc[4]) if len(row) > 4 else ""
            fis, diff, obs = parse_annotation(nota, qtd)
            records.append({"data_upload": now, "produto": prod, "categoria": classify_product(prod), "qtd_sistema": qtd, "qtd_fisica": fis, "diferenca": diff, "status": "ok" if diff==0 else "erro"})
        
        new_df = pd.DataFrame(records)
        conn = get_db()
        new_df.to_sql("contagens", conn, if_exists="append", index=False)
        st.session_state.df_cache = new_df
        st.session_state.processed_file = file.name
        st.rerun()

if not df.empty:
    # Filtros
    categorias = ["TODOS"] + sorted(df["categoria"].unique().tolist())
    escolha = st.radio("", categorias, horizontal=True)

    # MAPA (AQUI ESTÁ A CORREÇÃO PRINCIPAL)
    html_mapa = build_css_treemap(df, escolha)
    st.markdown(html_mapa, unsafe_allow_html=True)

    # Tabela de Erros
    st.markdown("### ⚠️ Divergências Detectadas")
    df_erro = df[df["diferenca"] != 0]
    if not df_erro.empty:
        st.dataframe(df_erro[["produto", "qtd_sistema", "qtd_fisica", "diferenca"]], use_container_width=True, hide_index=True)
    else:
        st.success("Tudo certo no estoque de Quirinópolis! 🚀")

else:
    st.info("Suba a planilha do BI para começar.")
