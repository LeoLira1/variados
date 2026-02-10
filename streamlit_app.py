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
if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

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
    .update-badge {
        font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
        color: #00d68f; text-align: center; margin-bottom: 0.5rem;
        opacity: 0.7;
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
    .stat-value.blue { color: #3b82f6; }
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

    .stPlotlyChart { border-radius: 12px; overflow: hidden; }

    .mode-indicator {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; margin-left: 6px;
    }
    .mode-mestre { background: #1e40af; color: #93c5fd; }
    .mode-parcial { background: #065f46; color: #6ee7b7; }
</style>
""", unsafe_allow_html=True)


# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camda_estoque.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    # Tabela Mestre — estado atual do estoque, 1 registro por código
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estoque_mestre (
            codigo TEXT PRIMARY KEY,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            qtd_sistema INTEGER NOT NULL DEFAULT 0,
            qtd_fisica INTEGER DEFAULT 0,
            diferenca INTEGER DEFAULT 0,
            nota TEXT DEFAULT '',
            status TEXT DEFAULT 'ok',
            ultima_contagem TEXT DEFAULT '',
            criado_em TEXT NOT NULL
        )
    """)
    # Log de uploads
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historico_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL,
            arquivo TEXT DEFAULT '',
            total_produtos_lote INTEGER DEFAULT 0,
            novos INTEGER DEFAULT 0,
            atualizados INTEGER DEFAULT 0,
            divergentes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def get_current_stock() -> pd.DataFrame:
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM estoque_mestre ORDER BY categoria, produto", conn)
    conn.close()
    return df


def get_stock_count() -> int:
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM estoque_mestre").fetchone()
    conn.close()
    return row[0] if row else 0


def reset_db():
    conn = get_db()
    conn.execute("DELETE FROM estoque_mestre")
    conn.execute("DELETE FROM historico_uploads")
    conn.commit()
    conn.close()


# ── Classificação e Parsing ──────────────────────────────────────────────────

def classify_product(name: str) -> str:
    n = str(name).upper()
    rules = [
        ("HERBICIDAS", ["HERBICIDA"]),
        ("FUNGICIDAS", ["FUNGICIDA"]),
        ("INSETICIDAS", ["INSETICIDA"]),
        ("NEMATICIDAS", ["NEMATICIDA"]),
        ("ADUBOS FOLIARES", ["ADUBO FOLIAR"]),
        ("ADUBOS QUÍMICOS", ["ADUBO Q"]),
        ("ÓLEOS", ["OLEO", "ÓLEO"]),
        ("SEMENTES", ["SEMENTE"]),
        ("ADJUVANTES", ["ADJUVANTE", "ESPALHANTE"]),
    ]
    for cat, keywords in rules:
        if any(kw in n for kw in keywords):
            return cat
    return "OUTROS"


def short_name(prod: str) -> str:
    prefixes = [
        "HERBICIDA ", "FUNGICIDA ", "INSETICIDA ", "NEMATICIDA ",
        "ADUBO FOLIAR ", "ADUBO Q.", "OLEO VEGETAL ", "OLEO MINERAL ",
        "ÓLEO VEGETAL ", "ÓLEO MINERAL ", "ADJUVANTE ", "SEMENTE ",
    ]
    up = str(prod).upper()
    for p in prefixes:
        if up.startswith(p):
            return str(prod)[len(p):].strip()
    return str(prod)


def parse_annotation(nota: str, qtd_sistema: int) -> tuple:
    """Retorna: (qtd_fisica, diferenca, observacao, status_type)"""
    if not nota or str(nota).strip().lower() in ["", "nan", "none"]:
        return (qtd_sistema, 0, "", "ok")

    text = str(nota).strip().lower()

    # Falta
    m = re.match(r"falta\s+(\d+)\s*(.*)", text)
    if m:
        falta = int(m.group(1))
        return (qtd_sistema - falta, -falta, m.group(2).strip(), "falta")

    # Sobra
    m = re.match(r"(pass|sobr)(?:a|ando)\s+(\d+)\s*(.*)", text)
    if m:
        sobra = int(m.group(2))
        return (qtd_sistema + sobra, +sobra, m.group(3).strip(), "sobra")

    # Danificados
    keywords_danificado = [
        "danificado", "avaria", "quebrado", "defeito",
        "vencido", "improprio", "vazando",
    ]
    if any(k in text for k in keywords_danificado):
        return (qtd_sistema, 0, str(nota).strip(), "danificado")

    return (qtd_sistema, 0, str(nota).strip(), "ok")


# ── Leitura de Planilha (compartilhada) ──────────────────────────────────────

def read_excel_to_records(uploaded_file) -> tuple:
    """
    Lê uma planilha XLSX e retorna (ok, msg_ou_records).
    Se ok=True, retorna lista de dicts com as colunas padronizadas.
    Se ok=False, retorna mensagem de erro.
    """
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception as e:
        return (False, f"Erro ao ler arquivo: {e}")

    # Localiza cabeçalho
    header_idx = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().upper() for v in row.tolist()]
        if any(v == "PRODUTO" for v in vals) and any("QUANTIDADE" in v or v == "QTD" for v in vals):
            header_idx = i
            break

    if header_idx is None:
        return (False, "Cabeçalho não encontrado. Preciso de colunas 'Produto' e 'Quantidade'.")

    df = df_raw.iloc[header_idx + 1:].copy()
    raw_cols = df_raw.iloc[header_idx].tolist()
    df.columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(raw_cols)]

    # Detecta colunas
    col_prod, col_qtd, col_cod, col_nota = None, None, None, None
    for c in df.columns:
        cu = c.upper()
        if "PRODUTO" in cu and col_prod is None:
            col_prod = c
        elif ("QUANTIDADE" in cu or cu == "QTD") and col_qtd is None:
            col_qtd = c
        elif ("CÓDIGO" in cu or "CODIGO" in cu or cu == "COD") and col_cod is None:
            col_cod = c
        if ("OBS" in cu or "NOTA" in cu or "DIFEREN" in cu) and col_nota is None:
            col_nota = c

    # Fallback: se não achou coluna de nota, usa a 5ª coluna
    if col_nota is None and len(df.columns) >= 5:
        col_nota = df.columns[4]

    if col_prod is None or col_qtd is None:
        return (False, "Colunas obrigatórias 'Produto' e 'Quantidade' não encontradas.")

    records = []
    for _, row in df.iterrows():
        produto = str(row.get(col_prod, "")).strip()
        if produto.upper() in ["", "NAN", "NONE", "TOTAL", "PRODUTO"]:
            continue

        try:
            raw_val = row.get(col_qtd)
            if pd.isna(raw_val):
                continue
            qtd_sistema = int(float(raw_val))
            if qtd_sistema <= 0:
                continue
        except (ValueError, TypeError):
            continue

        # Código — gera um baseado no nome se não existir
        codigo = ""
        if col_cod:
            codigo = str(row.get(col_cod, "")).strip()
            if codigo.upper() in ["NAN", "NONE", ""]:
                codigo = ""

        if not codigo:
            # Gera código determinístico a partir do nome do produto
            codigo = "AUTO_" + re.sub(r"[^A-Z0-9]", "", produto.upper())[:20]

        # Nota/Observação
        nota_raw = ""
        if col_nota:
            nota_raw = str(row.get(col_nota, "")).strip()
            if nota_raw.upper() in ["NAN", "NONE"]:
                nota_raw = ""
            # Se é só um número puro, ignora (provavelmente é outra coluna numérica)
            if re.match(r"^\d+([.,]\d+)?$", nota_raw):
                nota_raw = ""

        categoria = classify_product(produto)
        qtd_fisica, diferenca, observacao, status = parse_annotation(nota_raw, qtd_sistema)

        records.append({
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
        return (False, "Nenhum dado válido encontrado na planilha.")

    return (True, records)


# ── Upload Mestre (carga inicial / substituição total) ───────────────────────

def upload_mestre(uploaded_file) -> tuple:
    ok, result = read_excel_to_records(uploaded_file)
    if not ok:
        return (False, result)

    records = result
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Limpa o mestre antes de carregar
    conn.execute("DELETE FROM estoque_mestre")

    for r in records:
        conn.execute("""
            INSERT INTO estoque_mestre
                (codigo, produto, categoria, qtd_sistema, qtd_fisica, diferenca, nota, status, ultima_contagem, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["codigo"], r["produto"], r["categoria"],
            r["qtd_sistema"], r["qtd_fisica"], r["diferenca"],
            r["nota"], r["status"], now, now,
        ))

    n_div = sum(1 for r in records if r["status"] != "ok")
    conn.execute("""
        INSERT INTO historico_uploads (data, tipo, arquivo, total_produtos_lote, novos, atualizados, divergentes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, "MESTRE", uploaded_file.name, len(records), len(records), 0, n_div))

    conn.commit()
    conn.close()
    return (True, f"✅ Mestre carregado: {len(records)} produtos ({n_div} divergências)")


# ── Upload Parcial (atualiza apenas os produtos do lote) ─────────────────────

def upload_parcial(uploaded_file) -> tuple:
    ok, result = read_excel_to_records(uploaded_file)
    if not ok:
        return (False, result)

    records = result
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    novos = 0
    atualizados = 0

    for r in records:
        # Verifica se já existe
        existing = conn.execute(
            "SELECT codigo FROM estoque_mestre WHERE codigo = ?", (r["codigo"],)
        ).fetchone()

        if existing:
            # UPDATE — atualiza só os campos da contagem
            conn.execute("""
                UPDATE estoque_mestre SET
                    produto = ?,
                    categoria = ?,
                    qtd_sistema = ?,
                    qtd_fisica = ?,
                    diferenca = ?,
                    nota = ?,
                    status = ?,
                    ultima_contagem = ?
                WHERE codigo = ?
            """, (
                r["produto"], r["categoria"],
                r["qtd_sistema"], r["qtd_fisica"], r["diferenca"],
                r["nota"], r["status"], now,
                r["codigo"],
            ))
            atualizados += 1
        else:
            # INSERT — produto novo que não estava no mestre
            conn.execute("""
                INSERT INTO estoque_mestre
                    (codigo, produto, categoria, qtd_sistema, qtd_fisica, diferenca, nota, status, ultima_contagem, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["codigo"], r["produto"], r["categoria"],
                r["qtd_sistema"], r["qtd_fisica"], r["diferenca"],
                r["nota"], r["status"], now, now,
            ))
            novos += 1

    n_div = sum(1 for r in records if r["status"] != "ok")
    conn.execute("""
        INSERT INTO historico_uploads (data, tipo, arquivo, total_produtos_lote, novos, atualizados, divergentes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, "PARCIAL", uploaded_file.name, len(records), novos, atualizados, n_div))

    conn.commit()
    conn.close()

    msg = f"✅ Parcial processada: {len(records)} produtos"
    if atualizados:
        msg += f" · {atualizados} atualizados"
    if novos:
        msg += f" · {novos} novos"
    if n_div:
        msg += f" · {n_div} divergências"

    return (True, msg)


# ── Treemap (Visualização Grid) ──────────────────────────────────────────────

def build_css_treemap(df: pd.DataFrame, filter_cat: str = "TODOS") -> str:
    if df.empty:
        return '<div style="color:#64748b; text-align:center; padding:40px;">Nenhum produto para exibir</div>'

    if filter_cat != "TODOS":
        df = df[df["categoria"] == filter_cat]
    if df.empty:
        return '<div style="color:#64748b; text-align:center; padding:40px;">Nenhum produto nesta categoria</div>'

    df = df.copy()
    df["qtd_sistema"] = pd.to_numeric(df["qtd_sistema"], errors="coerce").fillna(0)

    categories = {}
    for _, row in df.iterrows():
        cat = row["categoria"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(row)

    sorted_cats = sorted(
        categories.keys(),
        key=lambda c: sum(int(r["qtd_sistema"]) for r in categories[c]),
        reverse=True,
    )
    blocks_html = ""

    for cat in sorted_cats:
        rows = categories[cat]
        products_html = ""

        for r in sorted(rows, key=lambda x: str(x["produto"])):
            qs = int(r["qtd_sistema"])
            qf = int(r["qtd_fisica"]) if pd.notnull(r.get("qtd_fisica")) else qs
            diff = int(r["diferenca"]) if pd.notnull(r.get("diferenca")) else 0
            stat = str(r.get("status", "ok"))
            note = str(r.get("nota", "")) if pd.notnull(r.get("nota")) else ""
            cod = str(r.get("codigo", ""))

            # Cores e info
            if stat == "danificado":
                bg, txt = "#a55eea", "#fff"
                nums = re.findall(r"\d+", note)
                qtd_bad = nums[0] if nums else ""
                info = f"AVARIA: {qtd_bad}" if qtd_bad else "AVARIA"
            elif diff == 0:
                bg, txt = "#00d68f", "#0a2e1a"
                info = f"{qs}"
            elif diff < 0:
                bg, txt = "#ff4757", "#fff"
                info = f"{qf} (F {abs(diff)})"
            else:
                bg, txt = "#ffa502", "#fff"
                info = f"{qf} (S {diff})"

            # Indicador de "sem contagem recente"
            contagem = str(r.get("ultima_contagem", ""))
            border_extra = ""
            if not contagem or contagem in ["", "nan", "None"]:
                border_extra = "border: 2px dashed #64748b !important; opacity: 0.6;"

            tooltip = f"{r['produto']} | Cod: {cod} | Sist: {qs} | Fis: {qf}"
            if note:
                tooltip += f" | Obs: {note}"

            products_html += f"""
            <div style="width: 110px; height: 60px; background: {bg}; color: {txt};
                 border-radius: 4px; padding: 4px; margin: 2px;
                 display: flex; flex-direction: column; justify-content: center; align-items: center;
                 overflow: hidden; border: 1px solid rgba(0,0,0,0.1); {border_extra}"
                 title="{tooltip}">
                <div style="font-size: 0.55rem; font-weight: 700; text-align: center; width: 100%;
                     white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {short_name(r['produto'])}
                </div>
                <div style="font-size: 0.65rem; opacity: 0.9; font-family: monospace;
                     font-weight: bold; margin-top: 2px;">
                    {info}
                </div>
            </div>"""

        blocks_html += f"""
        <div style="width: 100%; background: #111827; border-radius: 8px; padding: 8px;
             margin-bottom: 8px; border: 1px solid #1e293b; display: flex; flex-direction: column;">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 700;
                 text-transform: uppercase; margin-bottom: 6px;
                 border-bottom: 1px solid #1e293b; padding-bottom: 4px;">
                {cat} <span style="font-size:0.6rem; color:#4a5568; font-weight:400;">({len(rows)})</span>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 2px;">{products_html}</div>
        </div>"""

    return f'<div style="display: flex; flex-direction: column; min-height: 450px;">{blocks_html}</div>'


# ── MAIN APP ─────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">CAMDA ESTOQUE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ESTOQUE MESTRE · QUIRINÓPOLIS</div>', unsafe_allow_html=True)

stock_count = get_stock_count()
has_mestre = stock_count > 0

# ── Upload Section ───────────────────────────────────────────────────────────
with st.expander("📤 Upload de Planilha", expanded=not has_mestre):

    if not has_mestre:
        st.info("👋 Nenhum estoque cadastrado. Faça o upload da planilha mestre para começar.")

    # Seleção do tipo de upload
    upload_mode = st.radio(
        "Tipo de Upload",
        ["🔵 Mestre (carga completa)" if not has_mestre else "🔵 Mestre (substituir tudo)",
         "🟢 Parcial (atualizar contagem do dia)"],
        index=0 if not has_mestre else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    is_mestre_upload = "Mestre" in upload_mode

    if is_mestre_upload:
        st.caption("O upload mestre substitui todo o estoque. Use para carga inicial ou recomecar do zero.")
    else:
        st.caption("O upload parcial atualiza apenas os produtos presentes na planilha. Os demais permanecem inalterados.")

    uploaded = st.file_uploader(
        "Planilha XLSX",
        type=["xlsx", "xls"],
  
