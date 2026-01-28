import streamlit as st
import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote
import random
import pytz

# Configuração da página
st.set_page_config(
    page_title="Dashboard Pessoal",
    page_icon="🌙",
    layout="wide"
)

# --- CSS GLASSMORPHISM CINEMATOGRÁFICO ---
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
    
    /* Cards com imagem de fundo */
    .card-with-bg {
        background-size: cover;
        background-position: center;
        position: relative;
        min-height: 140px;
    }
    
    .card-with-bg::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, 
            rgba(26, 26, 46, 0.7) 0%, 
            rgba(26, 26, 46, 0.5) 100%);
        backdrop-filter: blur(2px);
        border-radius: 24px;
        z-index: 0;
    }
    
    .card-with-bg > * {
        position: relative;
        z-index: 1;
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
    
    /* Filme/Série card especial */
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
    
    /* Efeito shimmer sutil */
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    .shimmer-effect {
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(255, 255, 255, 0.05) 50%, 
            transparent 100%);
        background-size: 200% 100%;
        animation: shimmer 3s ease-in-out infinite;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .card-value { font-size: 1.6rem; }
        .card-value-lg { font-size: 2rem; }
        .block-container { padding: 1rem !important; }
    }
</style>

<!-- Orbes decorativas -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
""", unsafe_allow_html=True)

# --- CARTEIRA BRASILEIRA (ticker: qtd, pm) ---
CARTEIRA_BR = {
    "PRIO3.SA": (267, 42.38),
    "ALUP11.SA": (159, 28.79),
    "BBAS3.SA": (236, 27.24),
    "MOVI3.SA": (290, 6.82),
    "AGRO3.SA": (135, 24.98),
    "VALE3.SA": (25, 61.38),
    "VAMO3.SA": (226, 6.75),
    "BBSE3.SA": (19, 33.30),
    "FESA4.SA": (95, 8.14),
    "SLCE3.SA": (31, 18.00),
    "TTEN3.SA": (17, 14.61),
    "JALL3.SA": (43, 4.65),
    "AMOB3.SA": (3, 0.00),
    "GARE11.SA": (142, 9.10),
    "KNCR11.SA": (9, 103.30),
}

# --- CARTEIRA AMERICANA (ticker: qtd, pm em USD) ---
CARTEIRA_US = {
    "VOO": (0.89425, 475.26),
    "QQQ": (0.54245, 456.28),
    "TSLA": (0.52762, 205.26),
    "VNQ": (2.73961, 82.48),
    "OKLO": (2.0, 9.75),
    "VT": (1.0785, 112.68),
    "VTI": (0.43415, 264.89),
    "SLYV": (1.42787, 80.54),
    "GOOGL": (0.32828, 174.61),
    "IWD": (0.34465, 174.09),
    "DIA": (0.1373, 400.58),
    "DVY": (0.46175, 121.34),
    "META": (0.08487, 541.77),
    "BLK": (0.04487, 891.02),
    "DE": (0.10018, 399.28),
    "NVDA": (0.2276, 87.79),
    "CAT": (0.07084, 352.91),
    "AMD": (0.19059, 157.41),
    "NUE": (0.14525, 172.12),
    "COP": (0.24956, 120.21),
    "DTE": (0.12989, 115.48),
    "MSFT": (0.02586, 409.90),
    "GLD": (0.08304, 240.85),
    "NXE": (3.32257, 7.52),
    "XOM": (0.33901, 117.99),
    "SPY": (0.0546, 549.27),
    "JNJ": (0.13323, 150.12),
    "MPC": (0.14027, 178.23),
    "AMZN": (0.05482, 182.42),
    "DUK": (0.09776, 102.29),
    "NEE": (0.13274, 75.34),
    "DVN": (0.26214, 38.15),
    "JPM": (0.02529, 197.71),
    "MAGS": (0.09928, 54.19),
    "INTR": (0.77762, 6.43),
}

# --- FUNÇÕES COM CACHE ---

@st.cache_data(ttl=900)
def get_weather(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "timezone": "America/Sao_Paulo"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json().get("current", {})
        
        code = data.get("weather_code", 0)
        weather_map = {
            0: ("☀️", "Céu limpo"), 1: ("🌤️", "Parcialmente limpo"),
            2: ("⛅", "Parcialmente nublado"), 3: ("☁️", "Nublado"),
            45: ("🌫️", "Neblina"), 48: ("🌫️", "Neblina com geada"),
            51: ("🌦️", "Chuvisco leve"), 53: ("🌦️", "Chuvisco"),
            55: ("🌧️", "Chuvisco forte"), 61: ("🌧️", "Chuva leve"),
            63: ("🌧️", "Chuva moderada"), 65: ("🌧️", "Chuva forte"),
            80: ("🌦️", "Pancadas leves"), 81: ("🌧️", "Pancadas"),
            82: ("⛈️", "Pancadas fortes"), 95: ("⛈️", "Tempestade"),
        }
        
        icon, descricao = weather_map.get(code, ("❓", "Indisponível"))
        
        return {
            "temp": data.get("temperature_2m", "--"),
            "wind": data.get("wind_speed_10m", "--"),
            "humidity": data.get("relative_humidity_2m", "--"),
            "icon": icon,
            "descricao": descricao,
            "precipitacao": data.get("precipitation", 0)
        }
    except:
        return {"temp": "--", "wind": "--", "humidity": "--", "icon": "❓", "descricao": "Erro", "precipitacao": 0}

@st.cache_data(ttl=900)
def get_stock_data(ticker):
    try:
        acao = yf.Ticker(ticker)
        hist = acao.history(period="2d")
        if len(hist) >= 1:
            atual = hist['Close'].iloc[-1]
            anterior = hist['Close'].iloc[-2] if len(hist) > 1 else atual
            var = ((atual - anterior) / anterior) * 100
            return atual, var
        return 0.0, 0.0
    except:
        return 0.0, 0.0

@st.cache_data(ttl=900)
def get_dolar():
    try:
        ticker = yf.Ticker("USDBRL=X")
        hist = ticker.history(period="1d")
        if len(hist) >= 1:
            return hist['Close'].iloc[-1]
        return 6.0
    except:
        return 6.0

@st.cache_data(ttl=900)
def calcular_variacao_carteira_br():
    variacao_total = 0.0
    patrimonio_atual = 0.0
    custo_total = 0.0
    
    for ticker, (qtd, pm) in CARTEIRA_BR.items():
        try:
            acao = yf.Ticker(ticker)
            hist = acao.history(period="2d")
            if len(hist) >= 1:
                preco_atual = hist['Close'].iloc[-1]
                preco_anterior = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
                variacao_dia = (preco_atual - preco_anterior) * qtd
                variacao_total += variacao_dia
                patrimonio_atual += preco_atual * qtd
                custo_total += pm * qtd
        except:
            continue
    
    lucro_total = patrimonio_atual - custo_total
    return variacao_total, patrimonio_atual, lucro_total

@st.cache_data(ttl=900)
def calcular_variacao_carteira_us():
    variacao_total = 0.0
    patrimonio_atual = 0.0
    custo_total = 0.0
    
    for ticker, (qtd, pm) in CARTEIRA_US.items():
        try:
            acao = yf.Ticker(ticker)
            hist = acao.history(period="2d")
            if len(hist) >= 1:
                preco_atual = hist['Close'].iloc[-1]
                preco_anterior = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
                variacao_dia = (preco_atual - preco_anterior) * qtd
                variacao_total += variacao_dia
                patrimonio_atual += preco_atual * qtd
                custo_total += pm * qtd
        except:
            continue
    
    lucro_total = patrimonio_atual - custo_total
    return variacao_total, patrimonio_atual, lucro_total

@st.cache_data(ttl=600)
def get_news(query):
    try:
        data_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        query_com_data = f"{query} after:{data_limite}"
        query_encoded = quote(query_com_data)
        url = f"https://news.google.com/rss/search?q={query_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        return feed.entries[:4]
    except:
        return []

@st.cache_data(ttl=600)
def get_single_news(query):
    try:
        data_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        query_com_data = f"{query} after:{data_limite}"
        query_encoded = quote(query_com_data)
        url = f"https://news.google.com/rss/search?q={query_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        if feed.entries:
            return feed.entries[0]
        return None
    except:
        return None

# --- TMDB API CONFIG ---
# Para usar a API do TMDB, crie uma conta em https://www.themoviedb.org/
# e gere sua API key em https://www.themoviedb.org/settings/api
# Depois cole sua chave abaixo:
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5NzhlZTAxMTg0NmZkNGEzODFlMjE5NzIxNDA3ZTcxMyIsIm5iZiI6MTc2OTI4NzY2NS41NDQsInN1YiI6IjY5NzUyZmYxMjBjYTQ5ZjZiOGFlMmYzOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5sSTiI-dCh5kfrqAFgGRLS4Ba-X_zv0twE6KnRDjf0g"  # Token de Leitura da API

# Mapeamento de gêneros do TMDB
TMDB_GENRES = {
    28: "Ação", 12: "Aventura", 16: "Animação", 35: "Comédia", 80: "Crime",
    99: "Documentário", 18: "Drama", 10751: "Família", 14: "Fantasia",
    36: "História", 27: "Terror", 10402: "Música", 9648: "Mistério",
    10749: "Romance", 878: "Ficção Científica", 10770: "Telefilme",
    53: "Suspense", 10752: "Guerra", 37: "Faroeste",
    10759: "Ação & Aventura", 10762: "Kids", 10763: "Notícias",
    10764: "Reality", 10765: "Sci-Fi & Fantasia", 10766: "Novela",
    10767: "Talk Show", 10768: "Guerra & Política"
}

@st.cache_data(ttl=3600)  # Cache de 1 hora
def get_tmdb_trending():
    """Busca filmes e séries em alta no TMDB"""
    if not TMDB_API_KEY:
        return None
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        
        resultados = []
        
        # Buscar filmes em alta
        url_movies = "https://api.themoviedb.org/3/trending/movie/week?language=pt-BR"
        response_movies = requests.get(url_movies, headers=headers, timeout=10)
        
        if response_movies.status_code == 200:
            movies = response_movies.json().get("results", [])[:6]
            for movie in movies:
                generos = [TMDB_GENRES.get(g, "") for g in movie.get("genre_ids", [])[:2]]
                genero_str = "/".join([g for g in generos if g]) or "Drama"
                resultados.append({
                    "titulo": movie.get("title", "Sem título"),
                    "tipo": "Filme",
                    "genero": genero_str,
                    "nota": f"{movie.get('vote_average', 0):.1f}",
                    "onde": "Em alta 🔥"
                })
        
        # Buscar séries em alta
        url_tv = "https://api.themoviedb.org/3/trending/tv/week?language=pt-BR"
        response_tv = requests.get(url_tv, headers=headers, timeout=10)
        
        if response_tv.status_code == 200:
            shows = response_tv.json().get("results", [])[:6]
            for show in shows:
                generos = [TMDB_GENRES.get(g, "") for g in show.get("genre_ids", [])[:2]]
                genero_str = "/".join([g for g in generos if g]) or "Drama"
                resultados.append({
                    "titulo": show.get("name", "Sem título"),
                    "tipo": "Série",
                    "genero": genero_str,
                    "nota": f"{show.get('vote_average', 0):.1f}",
                    "onde": "Em alta 🔥"
                })
        
        return resultados if resultados else None
        
    except Exception as e:
        return None

# Lista fallback caso a API não esteja configurada
INDICACOES_FALLBACK = [
    {"titulo": "Oppenheimer", "tipo": "Filme", "genero": "Drama/Histórico", "nota": "9.0", "onde": "Prime Video"},
    {"titulo": "Se7en", "tipo": "Filme", "genero": "Suspense/Crime", "nota": "8.6", "onde": "Netflix"},
    {"titulo": "Interestelar", "tipo": "Filme", "genero": "Ficção Científica", "nota": "8.7", "onde": "Prime Video"},
    {"titulo": "Clube da Luta", "tipo": "Filme", "genero": "Drama/Suspense", "nota": "8.8", "onde": "Star+"},
    {"titulo": "Parasita", "tipo": "Filme", "genero": "Suspense/Drama", "nota": "8.5", "onde": "Prime Video"},
    {"titulo": "A Origem", "tipo": "Filme", "genero": "Ficção Científica", "nota": "8.8", "onde": "HBO Max"},
    {"titulo": "Duna: Parte 2", "tipo": "Filme", "genero": "Ficção Científica", "nota": "8.8", "onde": "Max"},
    {"titulo": "Whiplash", "tipo": "Filme", "genero": "Drama/Musical", "nota": "8.5", "onde": "Prime Video"},
    {"titulo": "Breaking Bad", "tipo": "Série", "genero": "Drama/Crime", "nota": "9.5", "onde": "Netflix"},
    {"titulo": "Succession", "tipo": "Série", "genero": "Drama", "nota": "8.9", "onde": "Max"},
    {"titulo": "Dark", "tipo": "Série", "genero": "Ficção Científica", "nota": "8.7", "onde": "Netflix"},
    {"titulo": "Severance", "tipo": "Série", "genero": "Suspense/Ficção", "nota": "8.7", "onde": "Apple TV+"},
    {"titulo": "The Bear", "tipo": "Série", "genero": "Drama/Comédia", "nota": "8.6", "onde": "Star+"},
    {"titulo": "Shogun", "tipo": "Série", "genero": "Drama/Histórico", "nota": "8.7", "onde": "Star+"},
    {"titulo": "True Detective S1", "tipo": "Série", "genero": "Crime/Drama", "nota": "9.0", "onde": "Max"},
    {"titulo": "Chernobyl", "tipo": "Série", "genero": "Drama/Histórico", "nota": "9.4", "onde": "Max"},
    {"titulo": "The Last of Us", "tipo": "Série", "genero": "Drama/Ação", "nota": "8.8", "onde": "Max"},
]

EMPRESAS_IA = [
    {"nome": "OpenAI", "query": "OpenAI ChatGPT", "emoji": "🟢"},
    {"nome": "Claude", "query": "Anthropic Claude AI", "emoji": "🟠"},
    {"nome": "Gemini", "query": "Google Gemini", "emoji": "🔵"},
    {"nome": "DeepSeek", "query": "DeepSeek AI", "emoji": "🟣"},
]

# --- LAYOUT DO DASHBOARD ---

# Ajuste de fuso horário
fuso_brasilia = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_brasilia)
dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][agora.weekday()]

# Header
st.markdown("""
<div class="main-header">
    <div class="main-title">Dashboard</div>
    <div class="main-subtitle">Seu universo em um só lugar</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# LINHA 1: Data/Hora + Clima
# ═══════════════════════════════════════════════════════════════

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown(f"""
    <div class="glass-card glass-dark" style="text-align: center;">
        <div class="card-label" style="justify-content: center;">📅 {dia_semana}</div>
        <div class="card-value card-value-lg">{agora.strftime("%H:%M")}</div>
        <div class="card-subtitle">{agora.strftime("%d de %B, %Y")}</div>
    </div>
    """, unsafe_allow_html=True)

w_quiri = get_weather(-18.4486, -50.4519)
w_coru = get_weather(-10.1264, -36.1756)

with col2:
    precip = f" · {w_quiri['precipitacao']}mm" if w_quiri['precipitacao'] > 0 else ""
    st.markdown(f"""
    <div class="glass-card glass-blue">
        <div class="card-label">📍 Quirinópolis, GO</div>
        <div class="card-value">{w_quiri['icon']} {w_quiri['temp']}°</div>
        <div class="card-subtitle">{w_quiri['descricao']}{precip}</div>
        <div class="card-subtitle" style="margin-top: 4px;">💨 {w_quiri['wind']} km/h · 💧 {w_quiri['humidity']}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    precip = f" · {w_coru['precipitacao']}mm" if w_coru['precipitacao'] > 0 else ""
    st.markdown(f"""
    <div class="glass-card glass-green">
        <div class="card-label">🌊 Coruripe, AL</div>
        <div class="card-value">{w_coru['icon']} {w_coru['temp']}°</div>
        <div class="card-subtitle">{w_coru['descricao']}{precip}</div>
        <div class="card-subtitle" style="margin-top: 4px;">💨 {w_coru['wind']} km/h · 💧 {w_coru['humidity']}%</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: CARTEIRA
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">💰</span> Minha Carteira</div>', unsafe_allow_html=True)

dolar = get_dolar()
var_br, patrim_br, lucro_br = calcular_variacao_carteira_br()
var_us, patrim_us, lucro_us = calcular_variacao_carteira_us()

var_us_brl = var_us * dolar
patrim_us_brl = patrim_us * dolar
lucro_us_brl = lucro_us * dolar

var_total_brl = var_br + var_us_brl
patrim_total = patrim_br + patrim_us_brl
lucro_total = lucro_br + lucro_us_brl

col_c1, col_c2, col_c3, col_c4 = st.columns(4)

with col_c1:
    badge_class = "badge-positive" if var_total_brl >= 0 else "badge-negative"
    symbol = "▲" if var_total_brl >= 0 else "▼"
    valor_cor = "#a8e6cf" if var_total_brl >= 0 else "#e6a8a8"
    st.markdown(f"""
    <div class="glass-card {'glass-green' if var_total_brl >= 0 else 'glass-rose'}">
        <div class="card-label">📊 Variação Hoje</div>
        <div class="card-value" style="color: {valor_cor};">{symbol} R$ {abs(var_total_brl):,.0f}</div>
        <div class="card-subtitle">BR: R$ {var_br:+,.0f} · US: R$ {var_us_brl:+,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_c2:
    badge_class = "badge-positive" if lucro_total >= 0 else "badge-negative"
    symbol = "▲" if lucro_total >= 0 else "▼"
    valor_cor = "#a8e6cf" if lucro_total >= 0 else "#e6a8a8"
    st.markdown(f"""
    <div class="glass-card {'glass-green' if lucro_total >= 0 else 'glass-rose'}">
        <div class="card-label">💎 Lucro vs PM</div>
        <div class="card-value" style="color: {valor_cor};">{symbol} R$ {abs(lucro_total):,.0f}</div>
        <div class="card-subtitle">BR: R$ {lucro_br:+,.0f} · US: R$ {lucro_us_brl:+,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_c3:
    ibov_price, ibov_var = get_stock_data("^BVSP")
    ibov_badge = "badge-positive" if ibov_var >= 0 else "badge-negative"
    ibov_symbol = "▲" if ibov_var >= 0 else "▼"
    ibov_cor = "#a8e6cf" if ibov_var >= 0 else "#e6a8a8"
    st.markdown(f"""
    <div class="glass-card glass-purple">
        <div class="card-label">🇧🇷 Ibovespa</div>
        <div class="card-value">{ibov_price:,.0f}</div>
        <div><span class="badge {ibov_badge}" style="color: {ibov_cor};">{ibov_symbol} {ibov_var:.2f}%</span></div>
    </div>
    """, unsafe_allow_html=True)

with col_c4:
    st.markdown(f"""
    <div class="glass-card glass-gold">
        <div class="card-label">💵 Dólar</div>
        <div class="card-value">R$ {dolar:.2f}</div>
        <div class="card-subtitle">Cotação atual</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: AÇÕES EM DESTAQUE
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">📈</span> Ações em Destaque</div>', unsafe_allow_html=True)

stocks = {
    "PRIO3": "PRIO3.SA", "BBAS3": "BBAS3.SA", "MOVI3": "MOVI3.SA",
    "VAMO3": "VAMO3.SA", "AGRO3": "AGRO3.SA", "DÓLAR": "USDBRL=X"
}

cols = st.columns(6)
for i, (name, ticker) in enumerate(stocks.items()):
    price, var = get_stock_data(ticker)
    badge_class = "badge-positive" if var >= 0 else "badge-negative"
    symbol = "▲" if var >= 0 else "▼"
    valor_cor = "#a8e6cf" if var >= 0 else "#e6a8a8"
    
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card glass-dark">
            <div class="card-label">{name}</div>
            <div class="card-value card-value-sm">R$ {price:.2f}</div>
            <div><span class="badge {badge_class}" style="color: {valor_cor};">{symbol} {var:.1f}%</span></div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: COMMODITIES
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">🌾</span> Commodities & Ativos</div>', unsafe_allow_html=True)

commodities = {
    "SOJA": ("SOYB", "🌱"), "MILHO": ("CORN", "🌽"), "CAFÉ": ("JO", "☕"),
    "BRENT": ("BNO", "🛢️"), "OURO": ("GLD", "💰"), "BITCOIN": ("BTC-USD", "₿")
}

glass_colors = ["glass-green", "glass-gold", "glass-rose", "glass-dark", "glass-gold", "glass-purple"]
cols = st.columns(6)

for i, (name, (ticker, emoji)) in enumerate(commodities.items()):
    price, var = get_stock_data(ticker)
    badge_class = "badge-positive" if var >= 0 else "badge-negative"
    symbol = "▲" if var >= 0 else "▼"
    valor_cor = "#a8e6cf" if var >= 0 else "#e6a8a8"
    
    price_display = f"${price:,.0f}" if name == "BITCOIN" else f"${price:.2f}"
    
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card {glass_colors[i]}">
            <div class="card-label">{emoji} {name}</div>
            <div class="card-value card-value-sm">{price_display}</div>
            <div><span class="badge {badge_class}" style="color: {valor_cor};">{symbol} {var:.1f}%</span></div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: IA & TECH
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">🤖</span> IA & Tech</div>', unsafe_allow_html=True)

cols_ia = st.columns(4)
glass_ia = ["glass-green", "glass-rose", "glass-blue", "glass-purple"]

for i, empresa in enumerate(EMPRESAS_IA):
    noticia = get_single_news(empresa["query"])
    
    with cols_ia[i]:
        if noticia:
            titulo = noticia.title[:55] + "..." if len(noticia.title) > 55 else noticia.title
            st.markdown(f"""
            <a href="{noticia.link}" target="_blank" style="text-decoration: none;">
                <div class="glass-card {glass_ia[i]}" style="min-height: 130px; cursor: pointer;">
                    <div class="card-label">{empresa['emoji']} {empresa['nome']}</div>
                    <div style="color: rgba(255,255,255,0.85); font-size: 0.9rem; line-height: 1.5;">{titulo}</div>
                    <div class="card-subtitle" style="margin-top: 8px;">Clique para ler →</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glass-card {glass_ia[i]}" style="min-height: 130px;">
                <div class="card-label">{empresa['emoji']} {empresa['nome']}</div>
                <div class="card-subtitle">Sem notícias recentes</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: FILMES & SÉRIES
# ═══════════════════════════════════════════════════════════════

# Tentar buscar do TMDB, senão usar fallback
tmdb_data = get_tmdb_trending()
if tmdb_data:
    indicacoes_dia = random.sample(tmdb_data, min(4, len(tmdb_data)))
    section_subtitle = "Em alta esta semana"
else:
    indicacoes_dia = random.sample(INDICACOES_FALLBACK, 4)
    section_subtitle = "Recomendações"

st.markdown(f'<div class="section-title"><span class="section-icon">🎬</span> Filmes & Séries · <span style="font-weight: 400; font-size: 0.85rem; opacity: 0.7;">{section_subtitle}</span></div>', unsafe_allow_html=True)
cols_f = st.columns(4)
glass_media = ["glass-purple", "glass-rose", "glass-blue", "glass-dark"]

for i, indicacao in enumerate(indicacoes_dia):
    emoji = "🎬" if indicacao["tipo"] == "Filme" else "📺"
    with cols_f[i]:
        st.markdown(f"""
        <div class="glass-card {glass_media[i]} media-card">
            <div class="media-rating">⭐ {indicacao['nota']}</div>
            <div class="card-label">{emoji} {indicacao['tipo']}</div>
            <div class="card-value card-value-sm" style="margin-top: 0.5rem;">{indicacao['titulo']}</div>
            <div class="card-subtitle" style="margin-top: 0.5rem;">{indicacao['genero']}</div>
            <div class="card-subtitle">{indicacao['onde']}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO: NOTÍCIAS REGIONAIS
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">📰</span> Notícias da Região</div>', unsafe_allow_html=True)

col_n1, col_n2 = st.columns(2)

with col_n1:
    st.markdown('<div class="card-label" style="margin-bottom: 1rem; font-size: 0.9rem;">🌴 CORURIPE & ALAGOAS</div>', unsafe_allow_html=True)
    news_al = get_news("Coruripe Alagoas")
    if news_al:
        for item in news_al:
            titulo = item.title[:80] + "..." if len(item.title) > 80 else item.title
            st.markdown(f'<div class="news-item"><a href="{item.link}" target="_blank">{titulo}</a></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="news-item"><span style="color: rgba(255,255,255,0.5);">Sem notícias recentes</span></div>', unsafe_allow_html=True)

with col_n2:
    st.markdown('<div class="card-label" style="margin-bottom: 1rem; font-size: 0.9rem;">📍 QUIRINÓPOLIS & GOIÁS</div>', unsafe_allow_html=True)
    news_go = get_news("Quirinópolis Goiás")
    if news_go:
        for item in news_go:
            titulo = item.title[:80] + "..." if len(item.title) > 80 else item.title
            st.markdown(f'<div class="news-item"><a href="{item.link}" target="_blank">{titulo}</a></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="news-item"><span style="color: rgba(255,255,255,0.5);">Sem notícias recentes</span></div>', unsafe_allow_html=True)

# Botão de atualização
st.markdown("<br>", unsafe_allow_html=True)
col_btn = st.columns([1, 1, 1])
with col_btn[1]:
    if st.button("🔄 Atualizar Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Footer sutil
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: rgba(255,255,255,0.3); font-size: 0.75rem;">
    Atualizado às {time} · Dados via Yahoo Finance & Open-Meteo
</div>
""".format(time=agora.strftime("%H:%M")), unsafe_allow_html=True)
