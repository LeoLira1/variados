import streamlit as st
import pandas as pd
import sqlite3
import re
import os
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAMDA Estoque Mestre",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State ────────────────────────────────────────────────────────────
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

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
    .stat-value.purple { color: #a55eea; }
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
    # Tabela Histórico (Log de uploads)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            total_produtos_lote INTEGER,
            total_divergentes INTEGER
        )
    """)
    # Tabela Mestre (O estado atual do estoque)
    # A chave primária é o CODIGO, ou seja, só pode ter 1 registro por código
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estoque_atual (
            codigo TEXT PRIMARY KEY,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            qtd_sistema INTEGER,
            qtd_fisica INTEGER,
            diferenca INTEGER,
            nota TEXT,
            status TEXT,
            ultima_atualizacao TEXT
        )
    """)
    conn.commit()
    return conn

def get_current_stock() -> pd.DataFrame:
    conn = get_db()
    # Pega tudo do estoque mestre
    df = pd.read_sql_query("SELECT * FROM estoque_atual", conn)
    conn.close()
    return df

def reset_db():
    conn = get_db()
    conn.execute("DELETE FROM estoque_atual")
    conn.execute("DELETE FROM historico")
    conn.commit()
    conn.close()

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
        return (qtd_sistema, 0, "", "ok")

    text = str(nota).strip().lower()
    
    # 1. Checa Falta
    m = re.match(r"falta\s+(\d+)\s*(.*)", text)
    if m:
        falta = int(m.group(1))
        return (qtd_sistema - falta, -falta, m.group(2).strip(), "falta")

    # 2. Checa Sobra
    m = re.match(r"(pass|sobr)(?:a|ando)\s+(\d+)\s*(.*)", text)
    if m:
        sobra = int(m.group(2))
        return (qtd_sistema + sobra, +sobra, m.group(3).strip(), "sobra")

    # 3. Checa Danificados
    keywords_danificado = ["danificado", "avaria", "quebrado", "defeito", "vencido", "improprio", "vazando"]
    if any(k in text for k in keywords_danificado):
        return (qtd_sistema, 0, str(nota).strip(), "danificado")

    return (qtd_sistema, 0, str(nota).strip(), "ok")

def update_stock(uploaded_file) -> tuple:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception as e:
        return (False, f"Erro ao ler arquivo: {e}")

    # Localiza cabeçalho
    header_idx = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().upper() for v in row.tolist()]
        if any(v == "PRODUTO" for v in vals) and any("QUANTIDADE" in v for v in vals):
            header_idx = i
            break

    if header_idx is None:
        return (False, "Colunas 'Produto' e 'Quantidade' não encontradas.")

    df = df_raw.iloc[header_idx + 1:].copy()
    raw_cols = df_raw.iloc[header_idx].tolist()
    df.columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(raw_cols)]

    col_prod, col_qtd, col_cod, col_nota = None, None, None, None
    for c in df.columns:
        cu = c.upper()
        if "PRODUTO" in cu and col_prod is None: col_prod = c
        elif ("QUANTIDADE" in cu or cu == "QTD") and col_qtd is None: col_qtd = c
        elif ("CÓDIGO" in cu or "CODIGO" in cu) and col_cod is None: col_cod = c
        if ("OBS" in cu or "NOTA" in cu or "DIFEREN" in cu) and col_nota is None: col_nota = c

    if col_nota is None and len(df.columns) >= 5: col_nota = df.columns[4]
    if col_prod is None or col_qtd is None or col_cod is None:
        return (False, "Faltou identificar as colunas obrigatórias (principalmente CÓDIGO).")

    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count_updated = 0
    count_diverg = 0

    for _, row in df.iterrows():
        # Validação básica
        codigo = str(row.get(col_cod, "")).strip()
        if not codigo or codigo.upper() in ["NAN", "NONE"]: continue

        produto = str(row.get(col_prod, "")).strip()
        
        try:
            raw_val = row.get(col_qtd)
            if pd.isna(raw_val): continue
            qtd_sistema = int(float(raw_val))
        except: continue

        nota_raw = ""
        if col_nota:
            nota_raw = str(row.get(col_nota, "")).strip()
            if re.match(r"^\d+([.,]\d+)?$", nota_raw): nota_raw = ""

        categoria = classify_product(produto)
        qtd_fisica, diferenca, observacao, status = parse_annotation(nota_raw, qtd_sistema)

        if status != "ok": count_diverg += 1
        count_updated += 1

        # UPSERT: Se existe o código, atualiza. Se não, insere.
        conn.execute("""
            INSERT INTO estoque_atual (codigo, produto, categoria, qtd_sistema, qtd_fisica, diferenca, nota, status, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(codigo) DO UPDATE SET
                produto=excluded.produto,
                qtd_sistema=excluded.qtd_sistema,
                qtd_fisica=excluded.qtd_fisica,
                diferenca=excluded.diferenca,
                nota=excluded.nota,
                status=excluded.status,
                ultima_atualizacao=excluded.ultima_atualizacao
        """, (codigo, produto, categoria, qtd_sistema, qtd_fisica, diferenca, observacao, status, now))

    conn.execute("INSERT INTO historico (data, total_produtos_lote, total_divergentes) VALUES (?,?,?)",
                 (now, count_updated, count_diverg))
    conn.commit()
    conn.close()

    return (True, f"Atualizado: {count_updated} produtos.")

# ── Treemap (Visualização Grid) ──────────────────────────────────────────────

def build_css_treemap(df: pd.DataFrame, filter_cat: str = "TODOS") -> str:
    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty: return ""

    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors='coerce').fillna(0)
    
    categories = {}
    for _, row in df.iterrows():
        cat = row["categoria"]
        if cat not in categories: categories[cat] = []
        categories[cat].append(row)

    sorted_cats = sorted(categories.keys(), key=lambda c: sum(int(r["qtd_sistema"]) for r in categories[c]), reverse=True)
    blocks_html = ""

    for cat in sorted_cats:
        rows = categories[cat]
        products_html = ""
        # Ordena por nome para facilitar encontrar visualmente no mestre
        for r in sorted(rows, key=lambda x: str(x["produto"])):
            qs = int(r["qtd_sistema"])
            qf = int(r["qtd_fisica"]) if pd.notnull(r["qtd_fisica"]) else qs
            diff = int(r["diferenca"])
            stat = r["status"]
            note = str(r["nota"]) if r["nota"] else ""
            
            # Cores
            if stat == "danificado":
                bg, txt = "#a55eea", "#fff"
                nums = re.findall(r'\d+', note)
                qtd_bad = nums[0] if nums else ""
                info = f"AVARIA: {qtd_bad}" if qtd_bad else "AVARIA"
            elif diff == 0:
                bg, txt = "#00d68f", "#0a2e1a"
                info = f"{qs}"
            elif diff < 0:
                bg, txt = "#ff4757", "#fff"
                info = f"{qf} (Falta {abs(diff)})"
            else:
                bg, txt = "#ffa502", "#fff"
                info = f"{qf} (Sobra {diff})"

            products_html += f"""
            <div style="width: 110px; height: 60px; background: {bg}; color: {txt}; 
                 border-radius: 4px; padding: 4px; margin: 2px; 
                 display: flex; flex-direction: column; justify-content: center; align-items: center;
                 overflow: hidden; border: 1px solid rgba(0,0,0,0.1);" title="{r['produto']} (Cod: {r['codigo']})">
                <div style="font-size: 0.55rem; font-weight: 700; text-align: center; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{short_name(r['produto'])}</div>
                <div style="font-size: 0.65rem; opacity: 0.9; font-family: monospace; font-weight: bold; margin-top: 2px;">{info}</div>
            </div>"""

        blocks_html += f"""
        <div style="width: 100%; background: #111827; border-radius: 8px; padding: 8px; 
             margin-bottom: 8px; border: 1px solid #1e293b; display: flex; flex-direction: column;">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">{cat}</div>
            <div style="display: flex; flex-wrap: wrap; gap: 2px;">{products_html}</div>
        </div>"""

    return f'<div style="display: flex; flex-direction: column; min-height: 450px;">{blocks_html}</div>'

# ── MAIN APP ─────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ESTOQUE MESTRE · ATUALIZAÇÃO PARCIAL</div>', unsafe_allow_html=True)

# Recupera o banco de dados inteiro (Mestre)
df_mestre = get_current_stock()

with st.expander("📤 Atualizar Estoque (Upload Parcial)", expanded=df_mestre.empty):
    uploaded = st.file_uploader("XLSX do Dia", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded:
        # Botão para confirmar processamento (evita processar 2x ao mudar aba)
        if st.button("Processar Atualização"):
            ok, msg = update_stock(uploaded)
            if ok:
                st.success(msg)
                st.session_state.last_update = datetime.now()
                st.rerun()
            else:
                st.error(msg)
    
    # Botão de Reset (escondido para segurança)
    if not df_mestre.empty:
        st.markdown("---")
        if st.button("⚠️ Limpar Banco de Dados (Começar do Zero)"):
            reset_db()
            st.rerun()

if not df_mestre.empty:
    search_term = st.text_input("🔍 Buscar no Mestre", placeholder="Nome ou Código...", label_visibility="collapsed")
    
    # Filtro de busca
    df_view = df_mestre.copy()
    if search_term:
        df_view = df_view[df_view["produto"].astype(str).str.contains(search_term, case=False, na=False) | 
                          df_view["codigo"].astype(str).str.contains(search_term, case=False, na=False)]

    # Estatísticas do ESTOQUE ATUAL
    n_falta = len(df_view[df_view["status"]=="falta"])
    n_sobra = len(df_view[df_view["status"]=="sobra"])
    n_danificado = len(df_view[df_view["status"]=="danificado"])

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card"><div class="stat-value">{len(df_view)}</div><div class="stat-label">Total Mestre</div></div>
        <div class="stat-card"><div class="stat-value">{len(df_view[df_view["status"]=="ok"])}</div><div class="stat-label">OK</div></div>
        <div class="stat-card"><div class="stat-value red">{n_falta}</div><div class="stat-label">Faltas</div></div>
        <div class="stat-card"><div class="stat-value amber">{n_sobra}</div><div class="stat-label">Sobras</div></div>
        <div class="stat-card"><div class="stat-value purple">{n_danificado}</div><div class="stat-label">Danificados</div></div>
    </div>
    """, unsafe_allow_html=True)

    cats = ["TODOS"] + sorted(df_view["categoria"].unique().tolist())
    f_cat = st.radio("Filtro", cats, horizontal=True, label_visibility="collapsed")
    
    t1, t2, t3, t4 = st.tabs(["🗺️ Estoque Atual", "⚠️ Divergências", "💔 Danificados", "📝 Log de Uploads"])
    
    with t1: st.markdown(build_css_treemap(df_view, f_cat), unsafe_allow_html=True)
    
    with t2: 
        df_div = df_view[(df_view["status"]=="falta") | (df_view["status"]=="sobra")]
        st.dataframe(df_div[["codigo", "produto", "qtd_sistema", "qtd_fisica", "diferenca", "ultima_atualizacao"]], hide_index=True, use_container_width=True)
    
    with t3:
        st.dataframe(df_view[df_view["status"]=="danificado"][["codigo", "produto", "qtd_sistema", "nota", "ultima_atualizacao"]], hide_index=True, use_container_width=True)

    with t4: 
        conn = get_db()
        st.table(pd.read_sql_query("SELECT * FROM historico ORDER BY id DESC LIMIT 10", conn))
        conn.close()
