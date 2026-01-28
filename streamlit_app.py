import streamlit as st
import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote
import random
import pytz
import locale

# Tentar configurar locale para português brasileiro
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass  # Usa fallback manual

# Mapeamento de meses em português (fallback)
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
DIAS_SEMANA_CURTO = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Configuração da página
st.set_page_config(
    page_title="Dashboard Pessoal",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS GLASSMORPHISM CINEMATOGRÁFICO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Reset e Base */
    .stApp {
        background: linear-gradient(135deg, 
            #1a1a2e 0%, 
            #16213e 25%,
            #1a1a2e 50%,
            #0f0f1a 75%,
            #1a1a2e 100%);
        background-attachment: fixed;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Efeito de partículas/estrelas no fundo */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.3), transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.4), transparent),
            radial-gradient(2px 2px at 130px 80px, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 160px 120px, rgba(255,255,255,0.3), transparent);
        background-repeat: repeat;
        background-size: 200px 200px;
        pointer-events: none;
        z-index: 0;
        opacity: 0.5;
    }
    
    /* Orbes decorativas flutuantes */
    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.4;
        pointer-events: none;
        z-index: 0;
    }
    .orb-1 {
        width: 300px;
        height: 300px;
        background: linear-gradient(135deg, #e8b4b8 0%, #d4a5a5 100%);
        top: 10%;
        right: 10%;
        animation: float 8s ease-in-out infinite;
    }
    .orb-2 {
        width: 200px;
        height: 200px;
        background: linear-gradient(135deg, #a5b4c4 0%, #7a8a9a 100%);
        bottom: 20%;
        left: 5%;
        animation: float 10s ease-in-out infinite reverse;
    }
    .orb-3 {
        width: 150px;
        height: 150px;
        background: linear-gradient(135deg, #c4a5d4 0%, #9a7aaa 100%);
        top: 50%;
        left: 30%;
        animation: float 12s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0) translateX(0); }
        25% { transform: translateY(-20px) translateX(10px); }
        50% { transform: translateY(-10px) translateX(-10px); }
        75% { transform: translateY(-30px) translateX(5px); }
    }
    
    /* Container principal */
    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
        position: relative;
        z-index: 1;
    }
    
    /* Esconder elementos padrão do Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === CARDS GLASSMORPHISM === */
    .glass-card {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.1) 0%, 
            rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: slideUp 0.6s ease-out forwards;
    }
    
    .glass-card:nth-child(1) { animation-delay: 0.1s; }
    .glass-card:nth-child(2) { animation-delay: 0.2s; }
    .glass-card:nth-child(3) { animation-delay: 0.3s; }
    .glass-card:nth-child(4) { animation-delay: 0.4s; }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.25);
    }
    
    /* Variantes de cor para cards */
    .glass-rose {
        background: linear-gradient(135deg, 
            rgba(232, 180, 184, 0.2) 0%, 
            rgba(180, 140, 144, 0.1) 100%);
    }
    
    .glass-blue {
        background: linear-gradient(135deg, 
            rgba(165, 180, 196, 0.2) 0%, 
            rgba(100, 120, 140, 0.1) 100%);
    }
    
    .glass-purple {
        background: linear-gradient(135deg, 
            rgba(196, 165, 212, 0.2) 0%, 
            rgba(140, 100, 160, 0.1) 100%);
    }
    
    .glass-gold {
        background: linear-gradient(135deg, 
            rgba(212, 180, 130, 0.2) 0%, 
            rgba(160, 130, 80, 0.1) 100%);
    }
    
    .glass-green {
        background: linear-gradient(135deg, 
            rgba(130, 180, 160, 0.2) 0%, 
            rgba(80, 130, 110, 0.1) 100%);
    }
    
    .glass-dark {
        background: linear-gradient(135deg, 
            rgba(60, 60, 80, 0.4) 0%, 
            rgba(40, 40, 60, 0.2) 100%);
    }
    
    /* Glow effects */
    .positive-glow {
        box-shadow: 
            0 0 20px rgba(67, 233, 123, 0.15),
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(67, 233, 123, 0.3);
    }
    
    .negative-glow {
        box-shadow: 
            0 0 20px rgba(255, 107, 107, 0.15),
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 107, 107, 0.3);
    }
    
    /* Tipografia */
    .card-label {
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .card-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.95);
        line-height: 1.2;
        margin-bottom: 0.3rem;
    }
    
    .card-value-lg {
        font-size: 2.8rem;
    }
    
    .card-value-sm {
        font-size: 1.4rem;
    }
    
    .card-subtitle {
        font-family: 'Outfit', sans-serif;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
        font-weight: 400;
    }
    
    /* Badges de variação */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 20px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
    }
    
    .badge-positive {
        background: rgba(130, 200, 160, 0.3);
        color: #a8e6cf;
        border: 1px solid rgba(130, 200, 160, 0.4);
    }
    
    .badge-negative {
        background: rgba(200, 130, 130, 0.3);
        color: #e6a8a8;
        border: 1px solid rgba(200, 130, 130, 0.4);
    }
    
    /* Seções */
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        margin: 2.5rem 0 1.2rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: 0.5px;
    }
    
    .section-icon {
        width: 32px;
        height: 32px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.15) 0%, 
            rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
    }
    
    /* Cards de notícias */
    .news-item {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.08) 0%, 
            rgba(255, 255, 255, 0.03) 100%);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .news-item::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #e8b4b8, #a5b4c4);
        border-radius: 3px;
    }
    
    .news-item:hover {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.12) 0%, 
            rgba(255, 255, 255, 0.06) 100%);
        transform: translateX(4px);
    }
    
    .news-item a {
        color: rgba(255, 255, 255, 0.85);
        text-decoration: none;
        font-family: 'Outfit', sans-serif;
        font-size: 0.9rem;
        font-weight: 400;
        line-height: 1.5;
        display: block;
    }
    
    .news-item a:hover {
        color: rgba(255, 255, 255, 1);
    }
    
    /* Header principal */
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 300;
        color: rgba(255, 255, 255, 0.9);
        letter-spacing: 8px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        font-family: 'Outfit', sans-serif;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.4);
        letter-spacing: 2px;
    }
    
    /* Botão de atualização */
    .stButton > button {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.1) 0%, 
            rgba(255, 255, 255, 0.05) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        color: rgba(255, 255, 255, 0.8) !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
        letter-spacing: 1px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.15) 0%, 
            rgba(255, 255, 255, 0.08) 100%) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Media Cards */
    .media-card {
        position: relative;
        overflow: hidden;
    }
    
    .media-rating {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        padding: 4px 10px;
        border-radius: 12px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: #ffd700;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.6);
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .card-value { font-size: 1.6rem; }
        .card-value-lg { font-size: 2rem; }
        .block-container { padding: 1rem !important; }
    }
    
    /* Sidebar estilizada */
    .css-1d391kg {
        background: rgba(0, 0, 0, 0.2);
    }
</style>

<!-- Orbes decorativas -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# CARTEIRAS DE INVESTIMENTO
# ═══════════════════════════════════════════════════════════════════
CARTEIRA_BR = {
    "PRIO3.SA": (267, 42.38), "ALUP11.SA": (159, 28.79), "BBAS3.SA": (236, 27.24),
    "MOVI3.SA": (290, 6.82), "AGRO3.SA": (135, 24.98), "VALE3.SA": (25, 61.38),
    "VAMO3.SA": (226, 6.75), "BBSE3.SA": (19, 33.30), "FESA4.SA": (95, 8.14),
    "SLCE3.SA": (31, 18.00), "TTEN3.SA": (17, 14.61), "JALL3.SA": (43, 4.65),
    "AMOB3.SA": (3, 0.00), "GARE11.SA": (142, 9.10), "KNCR11.SA": (9, 103.30),
}

CARTEIRA_US = {
    "VOO": (0.89425, 475.26), "QQQ": (0.54245, 456.28), "TSLA": (0.52762, 205.26),
    "VNQ": (2.73961, 82.48), "OKLO": (2.0, 9.75), "VT": (1.0785, 112.68),
    "VTI": (0.43415, 264.89), "SLYV": (1.42787, 80.54), "GOOGL": (0.32828, 174.61),
    "IWD": (0.34465, 174.09), "DIA": (0.1373, 400.58), "DVY": (0.46175, 121.34),
    "META": (0.08487, 541.77), "BLK": (0.04487, 891.02), "DE": (0.10018, 399.28),
    "NVDA": (0.2276, 87.79), "CAT": (0.07084, 352.91), "AMD": (0.19059, 157.41),
    "NUE": (0.14525, 172.12), "COP": (0.24956, 120.21), "DTE": (0.12989, 115.48),
    "MSFT": (0.02586, 409.90), "GLD": (0.08304, 240.85), "NXE": (3.32257, 7.52),
    "XOM": (0.33901, 117.99), "SPY": (0.0546, 549.27), "JNJ": (0.13323, 150.12),
    "MPC": (0.14027, 178.23), "AMZN": (0.05482, 182.42), "DUK": (0.09776, 102.29),
    "NEE": (0.13274, 75.34), "DVN": (0.26214, 38.15), "JPM": (0.02529, 197.71),
    "MAGS": (0.09928, 54.19), "INTR": (0.77762, 6.43),
}

# ═══════════════════════════════════════════════════════════════════
# DADOS AUXILIARES
# ═══════════════════════════════════════════════════════════════════
EMPRESAS_IA = [
    {"nome": "OpenAI", "query": "OpenAI ChatGPT", "emoji": "🟢", "cor": "glass-green"},
    {"nome": "Claude", "query": "Anthropic Claude AI", "emoji": "🟠", "cor": "glass-rose"},
    {"nome": "Gemini", "query": "Google Gemini", "emoji": "🔵", "cor": "glass-blue"},
    {"nome": "DeepSeek", "query": "DeepSeek AI", "emoji": "🟣", "cor": "glass-purple"},
]

INDICACOES_FALLBACK = [
    {"titulo": "Oppenheimer", "tipo": "Filme", "genero": "Drama/Histórico", "nota": "9.0", "onde": "Prime Video"},
    {"titulo": "Se7en", "tipo": "Filme", "genero": "Suspense/Crime", "nota": "8.6", "onde": "Netflix"},
    {"titulo": "Interestelar", "tipo": "Filme", "genero": "Ficção Científica", "nota": "8.7", "onde": "Prime Video"},
    {"titulo": "Dark", "tipo": "Série", "genero": "Ficção Científica", "nota": "8.7", "onde": "Netflix"},
    {"titulo": "Breaking Bad", "tipo": "Série", "genero": "Drama/Crime", "nota": "9.5", "onde": "Netflix"},
    {"titulo": "Severance", "tipo": "Série", "genero": "Suspense/Ficção", "nota": "8.7", "onde": "Apple TV+"},
    {"titulo": "The Bear", "tipo": "Série", "genero": "Drama/Comédia", "nota": "8.6", "onde": "Star+"},
    {"titulo": "Shogun", "tipo": "Série", "genero": "Drama/Histórico", "nota": "8.7", "onde": "Star+"},
]

CITACOES = [
    "O tempo é como um rio que leva tudo para frente. - Sêneca",
    "O mercado é um mecanismo de transferência de dinheiro dos impacientes para os pacientes. - Buffet",
    "Disciplina é a ponte entre metas e realizações.",
    "Na dúvida, não entre. - Jessé Livermore",
    "O melhor investimento é aquele que você entende.",
    "Paciência é amarga, mas seus frutos são doces. - Rousseau"
]

TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5NzhlZTAxMTg0NmZkNGEzODFlMjE5NzIxNDA3ZTcxMyIsIm5iZiI6MTc2OTI4NzY2NS41NDQsInN1YiI6IjY5NzUyZmYxMjBjYTQ5ZjZiOGFlMmYzOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5sSTiI-dCh5kfrqAFgGRLS4Ba-X_zv0twE6KnRDjf0g"

TMDB_GENRES = {
    28: "Ação", 12: "Aventura", 16: "Animação", 35: "Comédia", 80: "Crime",
    99: "Documentário", 18: "Drama", 10751: "Família", 14: "Fantasia",
    36: "História", 27: "Terror", 10402: "Música", 9648: "Mistério",
    10749: "Romance", 878: "Ficção Científica", 10759: "Ação & Aventura",
    10765: "Sci-Fi & Fantasia"
}

WEATHER_CODES = {
    0: ("☀️", "Céu limpo"), 1: ("🌤️", "Parcial"), 2: ("⛅", "Nublado"),
    3: ("☁️", "Fechado"), 45: ("🌫️", "Neblina"), 48: ("🌫️", "Neblina"),
    51: ("🌦️", "Chuvisco"), 53: ("🌦️", "Chuvisco"), 55: ("🌦️", "Chuvisco"),
    61: ("🌧️", "Chuva leve"), 63: ("🌧️", "Chuva"), 65: ("🌧️", "Chuva forte"),
    71: ("🌨️", "Neve leve"), 73: ("🌨️", "Neve"), 75: ("🌨️", "Neve forte"),
    80: ("🌦️", "Pancadas"), 81: ("🌦️", "Pancadas"), 82: ("🌦️", "Pancadas"),
    95: ("⛈️", "Tempestade"), 96: ("⛈️", "Tempestade"), 99: ("⛈️", "Tempestade")
}


# ═══════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════
def format_data_pt(dt: datetime) -> str:
    """Formata data em português brasileiro."""
    dia = dt.day
    mes = MESES_PT.get(dt.month, str(dt.month))
    ano = dt.year
    return f"{dia} de {mes}, {ano}"


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisão segura evitando divisão por zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def sparkline_svg(data: list, is_positive: bool = True) -> str:
    """Gera SVG de sparkline para visualização de tendência."""
    if not data or len(data) < 2:
        return ""
    
    try:
        color = "#a8e6cf" if is_positive else "#e6a8a8"
        width, height = 60, 25
        min_val, max_val = min(data), max(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        points = []
        for i, val in enumerate(data):
            x = (i / (len(data) - 1)) * width
            y = height - ((val - min_val) / range_val) * height * 0.8 - 2
            points.append(f"{x:.1f},{y:.1f}")
        
        last_point = points[-1].split(",")
        cx, cy = last_point[0], last_point[1]
        
        return f'''<svg width="{width}" height="{height}" style="opacity: 0.8;">
            <polyline points="{" ".join(points)}" fill="none" stroke="{color}" 
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="{cx}" cy="{cy}" r="2.5" fill="{color}"/>
        </svg>'''
    except (ValueError, IndexError, TypeError):
        return ""


# ═══════════════════════════════════════════════════════════════════
# FUNÇÕES DE DADOS COM CACHE
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=900)
def get_weather(lat: float, lon: float) -> dict:
    """Obtém dados climáticos atuais."""
    default = {
        "temp": "--", "wind": "--", "humidity": "--",
        "icon": "☁️", "descricao": "Indisponível", "precipitacao": 0
    }
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "timezone": "America/Sao_Paulo"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("current", {})
        
        code = data.get("weather_code", 0)
        icon, desc = WEATHER_CODES.get(code, ("☁️", "Nublado"))
        
        return {
            "temp": data.get("temperature_2m", "--"),
            "wind": data.get("wind_speed_10m", "--"),
            "humidity": data.get("relative_humidity_2m", "--"),
            "icon": icon,
            "descricao": desc,
            "precipitacao": data.get("precipitation", 0)
        }
    except requests.RequestException:
        return default
    except (KeyError, ValueError, TypeError):
        return default


@st.cache_data(ttl=3600)
def get_weather_forecast(lat: float, lon: float) -> dict:
    """Obtém previsão do tempo para os próximos dias."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "America/Sao_Paulo"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("daily", {})
    except requests.RequestException:
        return {}
    except (KeyError, ValueError):
        return {}


@st.cache_data(ttl=900)
def get_stock_data(ticker: str) -> tuple:
    """Obtém preço atual e variação de uma ação."""
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) >= 1:
            atual = float(hist['Close'].iloc[-1])
            anterior = float(hist['Close'].iloc[-2]) if len(hist) > 1 else atual
            variacao = safe_division((atual - anterior), anterior, 0) * 100
            return atual, variacao
        return 0.0, 0.0
    except Exception:
        return 0.0, 0.0


@st.cache_data(ttl=900)
def get_sparkline(ticker: str) -> list:
    """Obtém histórico de preços para sparkline."""
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if not hist.empty:
            return [float(x) for x in hist['Close'].tolist()]
        return []
    except Exception:
        return []


@st.cache_data(ttl=900)
def get_dolar() -> float:
    """Obtém cotação do dólar."""
    try:
        hist = yf.Ticker("USDBRL=X").history(period="1d")
        if len(hist) >= 1:
            return float(hist['Close'].iloc[-1])
        return 6.0
    except Exception:
        return 6.0


@st.cache_data(ttl=900)
def calcular_carteira(carteira: dict, dolar: float = 1.0) -> tuple:
    """Calcula variação, patrimônio e lucro da carteira."""
    variacao_total = 0.0
    patrimonio_total = 0.0
    custo_total = 0.0
    
    for ticker, (qtd, pm) in carteira.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 1:
                atual = float(hist['Close'].iloc[-1])
                anterior = float(hist['Close'].iloc[-2]) if len(hist) > 1 else atual
                variacao_total += (atual - anterior) * qtd * dolar
                patrimonio_total += atual * qtd * dolar
                custo_total += pm * qtd * dolar
        except Exception:
            continue
    
    lucro_total = patrimonio_total - custo_total
    return variacao_total, patrimonio_total, lucro_total


@st.cache_data(ttl=600)
def get_news(query: str, max_items: int = 4) -> list:
    """Obtém notícias do Google News RSS."""
    try:
        data_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        encoded_query = quote(f'{query} after:{data_limite}')
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        return feed.entries[:max_items]
    except requests.RequestException:
        return []
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_single_news(query: str):
    """Obtém uma única notícia do Google News RSS."""
    entries = get_news(query, max_items=1)
    return entries[0] if entries else None


@st.cache_data(ttl=3600)
def get_fear_greed() -> tuple:
    """Obtém índice Fear & Greed do mercado cripto."""
    try:
        response = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()['data'][0]
        return int(data['value']), data['value_classification']
    except requests.RequestException:
        return 50, "Neutral"
    except (KeyError, ValueError, IndexError):
        return 50, "Neutral"


@st.cache_data(ttl=3600)
def get_tmdb_trending() -> list:
    """Obtém filmes e séries em alta do TMDB."""
    if not TMDB_API_KEY:
        return []
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        resultados = []
        
        endpoints = [
            ("https://api.themoviedb.org/3/trending/movie/week?language=pt-BR", "Filme", "title"),
            ("https://api.themoviedb.org/3/trending/tv/week?language=pt-BR", "Série", "name")
        ]
        
        for url, tipo, title_key in endpoints:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                for item in response.json().get("results", [])[:6]:
                    generos = [TMDB_GENRES.get(g, "") for g in item.get("genre_ids", [])[:2]]
                    generos_str = "/".join([g for g in generos if g]) or "Drama"
                    nota = item.get('vote_average', 0)
                    
                    resultados.append({
                        "titulo": item.get(title_key, "Sem título"),
                        "tipo": tipo,
                        "genero": generos_str,
                        "nota": f"{nota:.1f}" if isinstance(nota, (int, float)) else "N/A",
                        "onde": "Em alta 🔥"
                    })
        
        return resultados
    except requests.RequestException:
        return []
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════
# HORA E DATA
# ═══════════════════════════════════════════════════════════════════
fuso_brasilia = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_brasilia)
dia_semana = DIAS_SEMANA_PT[agora.weekday()]
data_formatada = format_data_pt(agora)

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    citacao_dia = random.choice(CITACOES)
    st.markdown(f"""
    <div style="margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
        <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.8rem; opacity: 0.6; color: rgba(255,255,255,0.8);">
            💭 Reflexão do Dia
        </div>
        <div style="font-style: italic; font-size: 0.9rem; line-height: 1.5; color: rgba(255,255,255,0.85); font-family: 'Outfit', sans-serif;">
            "{citacao_dia}"
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <div class="main-title">Dashboard Pessoal</div>
    <div class="main-subtitle">Seu universo financeiro e cultural em um só lugar</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🏠 Visão Geral", "📊 Análise Detalhada", "🎬 Entretenimento & Tech"])

# ═══════════════════════════════════════════════════════════════════
# ABA 1: VISÃO GERAL
# ═══════════════════════════════════════════════════════════════════
with tab1:
    # DATA/CLIMA/HERO
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="glass-card glass-dark" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div class="card-label" style="justify-content: center;">📅 {dia_semana}</div>
            <div class="card-value card-value-lg">{agora.strftime("%H:%M")}</div>
            <div class="card-subtitle">{data_formatada}</div>
        </div>
        """, unsafe_allow_html=True)
    
    w_quiri = get_weather(-18.4486, -50.4519)
    with col2:
        precip = f" · {w_quiri['precipitacao']}mm" if w_quiri['precipitacao'] and w_quiri['precipitacao'] > 0 else ""
        st.markdown(f"""
        <div class="glass-card glass-blue">
            <div class="card-label">📍 Quirinópolis, GO</div>
            <div class="card-value">{w_quiri['icon']} {w_quiri['temp']}°</div>
            <div class="card-subtitle">{w_quiri['descricao']}{precip}</div>
            <div class="card-subtitle" style="margin-top: 4px;">💨 {w_quiri['wind']} km/h · 💧 {w_quiri['humidity']}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # PREVISÃO 5 DIAS
    forecast = get_weather_forecast(-18.4486, -50.4519)
    with col3:
        if forecast and "time" in forecast:
            dias_html = []
            num_dias = min(5, len(forecast.get("time", [])))
            
            for i in range(num_dias):
                try:
                    date = datetime.strptime(forecast["time"][i], "%Y-%m-%d")
                    day_name = DIAS_SEMANA_CURTO[date.weekday()]
                    code = forecast.get("weather_code", [0] * num_dias)[i]
                    emoji = WEATHER_CODES.get(code, ("☁️", ""))[0]
                    max_t = forecast.get("temperature_2m_max", [0] * num_dias)[i]
                    min_t = forecast.get("temperature_2m_min", [0] * num_dias)[i]
                    
                    dias_html.append(f"""
                    <div style="text-align: center; padding: 0.8rem 0.4rem; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); flex: 1;">
                        <div style="font-size: 0.65rem; opacity: 0.6; margin-bottom: 4px;">{day_name}</div>
                        <div style="font-size: 1.3rem; margin: 0.2rem 0;">{emoji}</div>
                        <div style="font-size: 0.75rem; font-weight: 500;">{max_t:.0f}° <span style="opacity: 0.4; font-size: 0.65rem;">{min_t:.0f}°</span></div>
                    </div>
                    """)
                except (ValueError, IndexError, TypeError):
                    continue
            
            if dias_html:
                st.markdown(f"""
                <div class="glass-card" style="padding: 1rem;">
                    <div class="card-label" style="margin-bottom: 0.8rem;">📅 Próximos 5 Dias</div>
                    <div style="display: flex; gap: 8px;">{"".join(dias_html)}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="glass-card"><div class="card-subtitle">Previsão indisponível</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="glass-card"><div class="card-subtitle">Previsão indisponível</div></div>', unsafe_allow_html=True)
    
    # HERO CARD CARTEIRA
    dolar = get_dolar()
    var_br, patrim_br, lucro_br = calcular_carteira(CARTEIRA_BR)
    var_us, patrim_us, lucro_us = calcular_carteira(CARTEIRA_US, dolar)
    var_total = var_br + var_us
    patrim_total = patrim_br + patrim_us
    lucro_total = lucro_br + lucro_us
    
    # Calcular porcentagens de alocação com segurança
    pct_br = safe_division(patrim_br, patrim_total, 0.5) * 100
    pct_us = safe_division(patrim_us, patrim_total, 0.5) * 100
    pct_lucro = min(safe_division(abs(lucro_total), patrim_total * 0.05, 0) * 100, 100) if patrim_total > 0 else 0
    
    glow_class = "positive-glow" if lucro_total >= 0 else "negative-glow"
    bg_color = "rgba(67, 233, 123, 0.15)" if lucro_total >= 0 else "rgba(255, 107, 107, 0.15)"
    border_color = "rgba(67, 233, 123, 0.3)" if lucro_total >= 0 else "rgba(255, 107, 107, 0.3)"
    var_color = "#a8e6cf" if var_total >= 0 else "#e6a8a8"
    lucro_color = "#a8e6cf" if lucro_total >= 0 else "#e6a8a8"
    gradient = "linear-gradient(90deg, #43e97b, #38f9d7)" if lucro_total >= 0 else "linear-gradient(90deg, #ff6b6b, #ee5a6f)"
    
    st.markdown(f"""
    <div class="glass-card {glow_class}" style="
        background: linear-gradient(135deg, {bg_color} 0%, rgba(30, 30, 60, 0.4) 100%);
        border: 1px solid {border_color};
        padding: 2rem; margin: 1.5rem 0;">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 2rem; text-align: center;">
            <div>
                <div class="card-label">Patrimônio Total</div>
                <div class="card-value card-value-lg">R$ {patrim_total:,.0f}</div>
                <div class="card-subtitle">Em BRL e USD</div>
            </div>
            <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 2rem;">
                <div class="card-label">Posição Hoje</div>
                <div class="card-value" style="color: {var_color};">
                    {'+' if var_total >= 0 else ''}R$ {var_total:,.0f}
                </div>
                <div class="card-subtitle">Variação diária</div>
            </div>
            <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 2rem;">
                <div class="card-label">Lucro/Prejuízo</div>
                <div class="card-value" style="color: {lucro_color};">
                    {'+' if lucro_total >= 0 else ''}R$ {lucro_total:,.0f}
                </div>
                <div class="card-subtitle">vs Preço Médio</div>
            </div>
            <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 2rem;">
                <div class="card-label">Cotação Dólar</div>
                <div class="card-value">R$ {dolar:.2f}</div>
                <div class="card-subtitle">USD/BRL</div>
            </div>
        </div>
        <div style="margin-top: 1.5rem; background: rgba(0,0,0,0.3); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="width: {pct_lucro}%; height: 100%; background: {gradient}; border-radius: 3px; transition: width 1s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # FEAR & GREED + CONVERSOR
    col_fg, col_conv = st.columns([1, 2])
    
    with col_fg:
        fear_val, fear_txt = get_fear_greed()
        gauge_color = f"hsl({fear_val * 1.2}, 70%, 50%)"
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; height: 100%;">
            <div class="card-label">🧠 Fear & Greed</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: {gauge_color}; margin: 0.5rem 0;">{fear_val}</div>
            <div style="background: linear-gradient(90deg, #e74c3c 0%, #f39c12 50%, #27ae60 100%); height: 6px; border-radius: 3px; position: relative; margin: 10px 0;">
                <div style="position: absolute; left: {fear_val}%; top: -3px; width: 12px; height: 12px; background: white; border-radius: 50%; box-shadow: 0 0 8px rgba(0,0,0,0.5); transform: translateX(-50%);"></div>
            </div>
            <div class="card-subtitle" style="text-transform: uppercase; letter-spacing: 1px; margin-top: 0.5rem;">{fear_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_conv:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label" style="margin-bottom: 1rem;">💱 Conversor Rápido</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            valor_conv = st.number_input("Valor", min_value=0.0, value=1000.0, label_visibility="collapsed", key="conv_val")
            moeda_origem = st.selectbox("Origem", ["USD", "BRL", "BTC"], index=0, label_visibility="collapsed", key="conv_from")
        with c2:
            st.markdown("<div style='text-align: center; padding-top: 1.2rem; font-size: 1.5rem; color: rgba(255,255,255,0.5);'>⇄</div>", unsafe_allow_html=True)
        with c3:
            moeda_dest = st.selectbox("Destino", ["BRL", "USD", "BTC"], index=0, label_visibility="collapsed", key="conv_to")
            
            btc_price, _ = get_stock_data("BTC-USD")
            btc_price = btc_price if btc_price > 0 else 100000  # Fallback
            
            # Taxas de conversão (tudo para USD como base)
            rates_to_usd = {"USD": 1.0, "BRL": 1.0 / dolar, "BTC": btc_price}
            rates_from_usd = {"USD": 1.0, "BRL": dolar, "BTC": 1.0 / btc_price}
            
            if moeda_origem == moeda_dest:
                resultado = valor_conv
            else:
                # Converter para USD primeiro, depois para moeda destino
                em_usd = valor_conv * rates_to_usd.get(moeda_origem, 1)
                resultado = em_usd * rates_from_usd.get(moeda_dest, 1)
            
            # Formatação do resultado
            if moeda_dest == "BTC":
                resultado_fmt = f"{resultado:.8f}"
            else:
                resultado_fmt = f"{resultado:,.2f}"
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 0.8rem; text-align: center; margin-top: 0.3rem; border: 1px solid rgba(255,255,255,0.1);">
                <div style="font-size: 1.5rem; font-weight: 600; color: #a8e6cf;">{resultado_fmt}</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">{moeda_dest}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # AÇÕES DESTAQUE COM SPARKLINES
    st.markdown('<div class="section-title"><span class="section-icon">📈</span> Ações em Destaque</div>', unsafe_allow_html=True)
    stocks_destaque = {
        "PRIO3": "PRIO3.SA", "BBAS3": "BBAS3.SA", "VALE3": "VALE3.SA",
        "MGLU3": "MGLU3.SA", "PETR4": "PETR4.SA", "ITUB4": "ITUB4.SA"
    }
    cols_st = st.columns(len(stocks_destaque))
    
    for i, (name, ticker) in enumerate(stocks_destaque.items()):
        price, var = get_stock_data(ticker)
        spark_data = get_sparkline(ticker)
        svg_spark = sparkline_svg(spark_data, is_positive=(var >= 0))
        glow = "positive-glow" if var >= 0 else "negative-glow"
        color = "#a8e6cf" if var >= 0 else "#e6a8a8"
        badge = "badge-positive" if var >= 0 else "badge-negative"
        arrow = "▲" if var >= 0 else "▼"
        
        with cols_st[i]:
            st.markdown(f"""
            <div class="glass-card glass-dark {glow}" style="position: relative; overflow: hidden;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div class="card-label">{name}</div>
                        <div class="card-value card-value-sm" style="color: {color};">R$ {price:.2f}</div>
                        <span class="badge {badge}">{arrow} {abs(var):.1f}%</span>
                    </div>
                    <div style="margin-top: -5px; margin-right: -10px;">{svg_spark}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABA 2: ANÁLISE DETALHADA
# ═══════════════════════════════════════════════════════════════════
with tab2:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # COMMODITIES
        st.markdown('<div class="section-title"><span class="section-icon">🌾</span> Commodities & Ativos</div>', unsafe_allow_html=True)
        commodities = {
            "SOJA": ("SOYB", "🌱", "glass-green"),
            "MILHO": ("CORN", "🌽", "glass-gold"),
            "CAFÉ": ("JO", "☕", "glass-rose"),
            "BRENT": ("BNO", "🛢️", "glass-dark"),
            "OURO": ("GLD", "💰", "glass-gold"),
            "BITCOIN": ("BTC-USD", "₿", "glass-purple")
        }
        cols_comm = st.columns(3)
        
        for i, (name, (ticker, emoji, cor)) in enumerate(commodities.items()):
            price, var = get_stock_data(ticker)
            price_display = f"${price:,.0f}" if name == "BITCOIN" else f"${price:.2f}"
            badge = "badge-positive" if var >= 0 else "badge-negative"
            arrow = "▲" if var >= 0 else "▼"
            
            with cols_comm[i % 3]:
                st.markdown(f"""
                <div class="glass-card {cor}">
                    <div class="card-label">{emoji} {name}</div>
                    <div style="display: flex; justify-content: space-between; align-items: end;">
                        <div>
                            <div class="card-value card-value-sm">{price_display}</div>
                            <span class="badge {badge}">{arrow} {abs(var):.1f}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # DIVIDENDOS PRÓXIMOS
        st.markdown('<div class="section-title"><span class="section-icon">💵</span> Próximos Proventos Estimados</div>', unsafe_allow_html=True)
        dividendos_mock = [
            {"ticker": "BBAS3", "data": "Fev/2025", "valor": "R$ 2,84", "tipo": "JCP", "cor": "glass-blue"},
            {"ticker": "BBSE3", "data": "Fev/2025", "valor": "R$ 1,15", "tipo": "DIV", "cor": "glass-gold"},
            {"ticker": "ITUB4", "data": "Mar/2025", "valor": "Est.", "tipo": "JCP", "cor": "glass-dark"},
            {"ticker": "PETR4", "data": "Mar/2025", "valor": "Est.", "tipo": "DIV", "cor": "glass-dark"},
        ]
        cols_div = st.columns(len(dividendos_mock))
        
        for col, div in zip(cols_div, dividendos_mock):
            with col:
                st.markdown(f"""
                <div class="glass-card {div['cor']}" style="text-align: center;">
                    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 600;">{div['ticker']}</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin: 0.3rem 0;">{div['data']}</div>
                    <div style="font-size: 1.1rem; color: #ffd700; font-weight: 500;">{div['valor']}</div>
                    <div style="font-size: 0.65rem; background: rgba(255,215,0,0.15); display: inline-block; padding: 2px 8px; border-radius: 10px; margin-top: 5px;">{div['tipo']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    with col_right:
        # DADOS DA CARTEIRA DETALHADOS
        st.markdown('<div class="section-title"><span class="section-icon">📋</span> Resumo</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card glass-blue">
            <div class="card-label">🇧🇷 Brasil</div>
            <div class="card-value">R$ {patrim_br:,.0f}</div>
            <div class="card-subtitle">Var: R$ {var_br:+,.0f}</div>
        </div>
        <div class="glass-card glass-purple">
            <div class="card-label">🇺🇸 EUA (em BRL)</div>
            <div class="card-value">R$ {patrim_us:,.0f}</div>
            <div class="card-subtitle">Var: R$ {var_us:+,.0f}</div>
        </div>
        <div class="glass-card glass-green">
            <div class="card-label">Alocação BR/US</div>
            <div style="margin-top: 0.5rem; background: rgba(0,0,0,0.3); height: 20px; border-radius: 10px; overflow: hidden; display: flex;">
                <div style="width: {pct_br}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                <div style="width: {pct_us}%; background: linear-gradient(90deg, #f093fb, #f5576c);"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.7rem; margin-top: 0.3rem; opacity: 0.7;">
                <span>🇧🇷 {pct_br:.0f}%</span>
                <span>🇺🇸 {pct_us:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # IBOVESPA
        ibov, ibov_var = get_stock_data("^BVSP")
        ibov_glow = "positive-glow" if ibov_var >= 0 else "negative-glow"
        ibov_badge = "badge-positive" if ibov_var >= 0 else "badge-negative"
        ibov_arrow = "▲" if ibov_var >= 0 else "▼"
        
        st.markdown(f"""
        <div class="glass-card {ibov_glow}">
            <div class="card-label">📊 Ibovespa</div>
            <div class="card-value">{ibov:,.0f}</div>
            <div class="badge {ibov_badge}" style="margin-top: 0.5rem;">
                {ibov_arrow} {abs(ibov_var):.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # NOTÍCIAS REGIONAIS
    st.markdown('<div class="section-title"><span class="section-icon">📰</span> Notícias Regionais</div>', unsafe_allow_html=True)
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        st.markdown('<div class="card-label" style="margin-bottom: 1rem; color: #a8e6cf;">🌴 Coruripe & Alagoas</div>', unsafe_allow_html=True)
        noticias_al = get_news("Coruripe Alagoas")
        if noticias_al:
            for item in noticias_al:
                titulo = item.title[:75] + "..." if len(item.title) > 75 else item.title
                link = getattr(item, 'link', '#')
                st.markdown(f'<div class="news-item"><a href="{link}" target="_blank">{titulo}</a></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card-subtitle">Sem notícias recentes</div>', unsafe_allow_html=True)
    
    with col_n2:
        st.markdown('<div class="card-label" style="margin-bottom: 1rem; color: #a8e6cf;">📍 Quirinópolis & Goiás</div>', unsafe_allow_html=True)
        noticias_go = get_news("Quirinópolis Goiás")
        if noticias_go:
            for item in noticias_go:
                titulo = item.title[:75] + "..." if len(item.title) > 75 else item.title
                link = getattr(item, 'link', '#')
                st.markdown(f'<div class="news-item"><a href="{link}" target="_blank">{titulo}</a></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card-subtitle">Sem notícias recentes</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABA 3: ENTRETENIMENTO E TECH
# ═══════════════════════════════════════════════════════════════════
with tab3:
    # NOTÍCIAS IA
    st.markdown('<div class="section-title"><span class="section-icon">🤖</span> Inteligência Artificial & Tech</div>', unsafe_allow_html=True)
    cols_ia = st.columns(4)
    
    for i, empresa in enumerate(EMPRESAS_IA):
        noticia = get_single_news(empresa["query"])
        with cols_ia[i]:
            if noticia:
                titulo = noticia.title[:50] + "..." if len(noticia.title) > 50 else noticia.title
                link = getattr(noticia, 'link', '#')
                st.markdown(f"""
                <a href="{link}" target="_blank" style="text-decoration: none;">
                    <div class="glass-card {empresa['cor']}" style="min-height: 140px; cursor: pointer;">
                        <div class="card-label">{empresa['emoji']} {empresa['nome']}</div>
                        <div style="color: rgba(255,255,255,0.9); font-size: 0.85rem; line-height: 1.4; margin-top: 0.5rem;">{titulo}</div>
                        <div style="margin-top: auto; padding-top: 1rem; font-size: 0.75rem; opacity: 0.6;">Ler mais →</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="glass-card {empresa['cor']}" style="min-height: 140px;">
                    <div class="card-label">{empresa['emoji']} {empresa['nome']}</div>
                    <div class="card-subtitle">Sem notícias recentes</div>
                </div>
                """, unsafe_allow_html=True)
    
    # FILMES E SÉRIES
    tmdb_data = get_tmdb_trending()
    
    if tmdb_data and len(tmdb_data) >= 4:
        indicacoes = random.sample(tmdb_data, min(4, len(tmdb_data)))
        subtitulo = "Em alta esta semana"
    else:
        indicacoes = random.sample(INDICACOES_FALLBACK, min(4, len(INDICACOES_FALLBACK)))
        subtitulo = "Recomendações"
    
    st.markdown(f'<div class="section-title"><span class="section-icon">🎬</span> Filmes & Séries · <span style="font-weight: 400; font-size: 0.85rem; opacity: 0.7;">{subtitulo}</span></div>', unsafe_allow_html=True)
    cols_f = st.columns(4)
    cores_media = ["glass-purple", "glass-rose", "glass-blue", "glass-dark"]
    
    for i, item in enumerate(indicacoes):
        emoji = "🎬" if item["tipo"] == "Filme" else "📺"
        cor = cores_media[i % len(cores_media)]
        onde_cor = "#a8e6cf" if "Em alta" in item.get("onde", "") else "rgba(255,215,0,0.8)"
        
        with cols_f[i]:
            st.markdown(f"""
            <div class="glass-card {cor} media-card" style="min-height: 160px;">
                <div class="media-rating">⭐ {item['nota']}</div>
                <div class="card-label">{emoji} {item['tipo']}</div>
                <div style="margin-top: 0.5rem; font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; color: rgba(255,255,255,0.95);">{item['titulo']}</div>
                <div class="card-subtitle" style="margin-top: 0.5rem;">{item['genero']}</div>
                <div class="card-subtitle" style="margin-top: 0.3rem; color: {onde_cor};">{item['onde']}</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; color: rgba(255,255,255,0.3); font-size: 0.75rem; border-top: 1px solid rgba(255,255,255,0.05);">
    <div style="margin-bottom: 0.5rem;">Atualizado às {agora.strftime("%H:%M")} · Dados via Yahoo Finance, Open-Meteo & Google News</div>
    <div style="font-size: 0.65rem; opacity: 0.7;">Dashboard Pessoal · 2025</div>
</div>
""", unsafe_allow_html=True)
