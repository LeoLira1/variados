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
    page_title="Dashboard de Entretenimento",
    page_icon="🎬",
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
    .orb-4 {
        width: 250px;
        height: 250px;
        background: linear-gradient(135deg, #b8d4a5 0%, #8aaa7a 100%);
        bottom: 10%;
        right: 20%;
        animation: float 15s ease-in-out infinite;
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
    
    .glass-red {
        background: linear-gradient(135deg, 
            rgba(212, 130, 130, 0.2) 0%, 
            rgba(160, 80, 80, 0.1) 100%);
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
    
    .badge-category {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.2);
        font-size: 0.7rem;
        text-transform: uppercase;
    }
    
    /* Seções */
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin: 2.5rem 0 1.2rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: 0.5px;
    }
    
    .section-icon {
        width: 36px;
        height: 36px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
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
    
    .news-meta {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 0.5rem;
        display: flex;
        gap: 1rem;
    }
    
    /* Cards com imagem de fundo */
    .card-with-bg {
        background-size: cover;
        background-position: center;
        position: relative;
        min-height: 160px;
    }
    
    .card-with-bg::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, 
            rgba(26, 26, 46, 0.8) 0%, 
            rgba(26, 26, 46, 0.6) 100%);
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
        font-size: 2rem;
        font-weight: 300;
        color: rgba(255, 255, 255, 0.9);
        letter-spacing: 8px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        font-family: 'Outfit', sans-serif;
        font-size: 0.9rem;
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
        min-height: 180px;
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
        z-index: 2;
    }
    
    .media-platform {
        position: absolute;
        top: 1rem;
        left: 1rem;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        z-index: 2;
    }
    
    /* Gaming card */
    .game-card {
        border-left: 3px solid;
        border-image: linear-gradient(180deg, #4ade80, #22d3ee) 1;
    }
    
    /* Book card */
    .book-card {
        border-left: 3px solid;
        border-image: linear-gradient(180deg, #fb923c, #f472b6) 1;
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
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        color: rgba(255, 255, 255, 0.6);
        font-family: 'Outfit', sans-serif;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .card-value { font-size: 1.6rem; }
        .card-value-lg { font-size: 2rem; }
        .block-container { padding: 1rem !important; }
        .main-title { font-size: 1.5rem; letter-spacing: 4px; }
    }
</style>

<!-- Orbes decorativas -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="orb orb-4"></div>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DE APIs ---
# TMDB - Crie sua chave em https://www.themoviedb.org/settings/api
TMDB_API_KEY = "sua_chave_aqui"  # Substitua pela sua chave da API TMDB

# RAWG API para jogos (opcional) - https://rawg.io/apidocs
RAWG_API_KEY = "sua_chave_rawg_aqui"  # Opcional para dados de jogos

# --- FUNÇÕES AUXILIARES ---

@st.cache_data(ttl=1800)
def get_news_by_topic(query, max_results=5, days=7):
    """Busca notícias por tópico usando Google News RSS"""
    try:
        data_limite = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query_com_data = f"{query} after:{data_limite}"
        query_encoded = quote(query_com_data)
        url = f"https://news.google.com/rss/search?q={query_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        return feed.entries[:max_results]
    except Exception as e:
        return []

@st.cache_data(ttl=3600)
def get_tmdb_trending():
    """Busca filmes e séries em alta no TMDB"""
    if not TMDB_API_KEY or TMDB_API_KEY == "sua_chave_aqui":
        return None
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }
        
        resultados = []
        
        # Filmes em alta
        url_movies = "https://api.themoviedb.org/3/trending/movie/week?language=pt-BR"
        response = requests.get(url_movies, headers=headers, timeout=10)
        
        if response.status_code == 200:
            movies = response.json().get("results", [])[:5]
            for movie in movies:
                resultados.append({
                    "titulo": movie.get("title", "Sem título"),
                    "tipo": "Filme",
                    "nota": f"{movie.get('vote_average', 0):.1f}",
                    "data": movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A",
                    "onde": "Cinema/Streaming"
                })
        
        # Séries em alta
        url_tv = "https://api.themoviedb.org/3/trending/tv/week?language=pt-BR"
        response = requests.get(url_tv, headers=headers, timeout=10)
        
        if response.status_code == 200:
            shows = response.json().get("results", [])[:5]
            for show in shows:
                resultados.append({
                    "titulo": show.get("name", "Sem título"),
                    "tipo": "Série",
                    "nota": f"{show.get('vote_average', 0):.1f}",
                    "data": show.get("first_air_date", "")[:4] if show.get("first_air_date") else "N/A",
                    "onde": "Streaming"
                })
        
        return resultados if resultados else None
        
    except Exception as e:
        return None

# --- DADOS FALLBACK ---

FALLBACK_MEDIA = [
    {"titulo": "Duna: Parte 2", "tipo": "Filme", "nota": "8.8", "data": "2024", "onde": "Max", "genero": "Ficção Científica"},
    {"titulo": "Deadpool & Wolverine", "tipo": "Filme", "nota": "8.1", "data": "2024", "onde": "Cinema", "genero": "Ação/Comédia"},
    {"titulo": "The Last of Us S2", "tipo": "Série", "nota": "8.5", "data": "2025", "onde": "Max", "genero": "Drama/Ação"},
    {"titulo": "Severance S2", "tipo": "Série", "nota": "8.9", "data": "2025", "onde": "Apple TV+", "genero": "Suspense"},
    {"titulo": "Wicked", "tipo": "Filme", "nota": "8.2", "data": "2024", "onde": "Cinema", "genero": "Musical"},
    {"titulo": "The Bear S3", "tipo": "Série", "nota": "8.6", "data": "2024", "onde": "Star+", "genero": "Drama"},
]

FALLBACK_GAMES = [
    {"titulo": "GTA VI", "plataforma": "PS5/Xbox", "genero": "Ação", "status": "Lançamento 2025"},
    {"titulo": "Death Stranding 2", "plataforma": "PS5", "genero": "Aventura", "status": "Previsto 2025"},
    {"titulo": "Hollow Knight: Silksong", "plataforma": "Multi", "genero": "Metroidvania", "status": "Em desenvolvimento"},
    {"titulo": "Borderlands 4", "plataforma": "Multi", "genero": "FPS/RPG", "status": "Anunciado"},
]

FALLBACK_BOOKS = [
    {"titulo": "A Paciente Silenciosa", "autor": "Alex Michaelides", "genero": "Thriller", "destaque": "Best-seller"},
    {"titulo": "O Hobbit", "autor": "J.R.R. Tolkien", "genero": "Fantasia", "destaque": "Clássico"},
    {"titulo": "1984", "autor": "George Orwell", "genero": "Distopia", "destaque": "Atemporal"},
]

# --- LAYOUT PRINCIPAL ---

fuso_brasilia = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_brasilia)
dia_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][agora.weekday()]

# Header
st.markdown(f"""
<div class="main-header">
    <div class="main-title">Pop Culture Hub</div>
    <div class="main-subtitle">Séries · Filmes · Jogos · Livros</div>
</div>
""", unsafe_allow_html=True)

# Data e Hora
col_time, col_empty = st.columns([1, 3])
with col_time:
    st.markdown(f"""
    <div class="glass-card glass-dark" style="text-align: center;">
        <div class="card-label" style="justify-content: center;">🗓️ {dia_semana}</div>
        <div class="card-value">{agora.strftime("%H:%M")}</div>
        <div class="card-subtitle">{agora.strftime("%d de %B, %Y")}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO 1: FILMES & SÉRIES (TMDB + Notícias)
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">🎬</span> Filmes & Séries em Alta</div>', unsafe_allow_html=True)

# Buscar dados do TMDB
tmdb_data = get_tmdb_trending()
if tmdb_data:
    media_items = random.sample(tmdb_data, min(4, len(tmdb_data)))
    using_tmdb = True
else:
    media_items = random.sample(FALLBACK_MEDIA, 4)
    using_tmdb = False

cols_media = st.columns(4)
glass_media = ["glass-purple", "glass-rose", "glass-blue", "glass-gold"]

for i, item in enumerate(media_items):
    with cols_media[i]:
        emoji = "🎬" if item["tipo"] == "Filme" else "📺"
        plataforma = item.get("onde", "Streaming")
        
        st.markdown(f"""
        <div class="glass-card {glass_media[i]} media-card">
            <div class="media-platform">{plataforma}</div>
            <div class="media-rating">⭐ {item['nota']}</div>
            <div style="margin-top: 2.5rem;">
                <div class="card-label">{emoji} {item['tipo']} · {item.get('data', 'N/A')}</div>
                <div class="card-value card-value-sm">{item['titulo']}</div>
                <div class="card-subtitle" style="margin-top: 0.5rem;">{item.get('genero', 'Drama')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Notícias sobre Cinema e Streaming
st.markdown("#### 📰 Últimas Notícias do Mundo do Entretenimento")

col_news1, col_news2 = st.columns(2)

with col_news1:
    news_movies = get_news_by_topic("lançamentos cinema filmes 2024 2025", max_results=4)
    if news_movies:
        for item in news_movies[:4]:
            titulo = item.title[:100] + "..." if len(item.title) > 100 else item.title
            st.markdown(f"""
            <div class="news-item">
                <a href="{item.link}" target="_blank">{titulo}</a>
                <div class="news-meta">🎬 Cinema · {item.get('published', 'Agora')[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Sem notícias recentes sobre cinema")

with col_news2:
    news_series = get_news_by_topic("séries Netflix HBO Max Disney streaming", max_results=4)
    if news_series:
        for item in news_series[:4]:
            titulo = item.title[:100] + "..." if len(item.title) > 100 else item.title
            st.markdown(f"""
            <div class="news-item">
                <a href="{item.link}" target="_blank">{titulo}</a>
                <div class="news-meta">📺 Streaming · {item.get('published', 'Agora')[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Sem notícias recentes sobre séries")

# ═══════════════════════════════════════════════════════════════
# SEÇÃO 2: JOGOS (Lançamentos + Notícias)
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">🎮</span> Lançamentos & Notícias de Games</div>', unsafe_allow_html=True)

# Cards de jogos aguardados
cols_games = st.columns(4)
glass_games = ["glass-green", "glass-blue", "glass-red", "glass-purple"]

for i, game in enumerate(FALLBACK_GAMES):
    with cols_games[i]:
        st.markdown(f"""
        <div class="glass-card {glass_games[i]} game-card" style="min-height: 150px;">
            <div style="position: absolute; top: 1rem; right: 1rem;">
                <span class="badge badge-category">🎯 {game['genero']}</span>
            </div>
            <div class="card-label" style="margin-top: 0.5rem;">🎮 {game['plataforma']}</div>
            <div class="card-value card-value-sm" style="margin-top: 0.5rem;">{game['titulo']}</div>
            <div class="card-subtitle" style="margin-top: 0.5rem; color: #4ade80;">{game['status']}</div>
        </div>
        """, unsafe_allow_html=True)

# Notícias sobre Jogos
st.markdown("#### 🎯 Últimas Notícias da Indústria de Games")

col_game_news1, col_game_news2 = st.columns(2)

with col_game_news1:
    news_ps5 = get_news_by_topic("PlayStation 5 PS5 jogos lançamentos", max_results=4, days=7)
    if news_ps5:
        for item in news_ps5[:4]:
            titulo = item.title[:90] + "..." if len(item.title) > 90 else item.title
            st.markdown(f"""
            <div class="news-item" style="border-left-color: #4ade80;">
                <a href="{item.link}" target="_blank">{titulo}</a>
                <div class="news-meta">🎮 PlayStation · {item.get('published', 'Agora')[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card glass-dark">
            <div class="card-subtitle">Sem atualizações recentes sobre PlayStation</div>
        </div>
        """, unsafe_allow_html=True)

with col_game_news2:
    news_xbox = get_news_by_topic("Xbox Series X Nintendo Switch jogos", max_results=4, days=7)
    if news_xbox:
        for item in news_xbox[:4]:
            titulo = item.title[:90] + "..." if len(item.title) > 90 else item.title
            st.markdown(f"""
            <div class="news-item" style="border-left-color: #22d3ee;">
                <a href="{item.link}" target="_blank">{titulo}</a>
                <div class="news-meta">🎯 Xbox/Nintendo · {item.get('published', 'Agora')[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card glass-dark">
            <div class="card-subtitle">Sem atualizações recentes sobre Xbox/Nintendo</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SEÇÃO 3: LIVROS (Lançamentos + Literatura)
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">📚</span> Literatura & Lançamentos Literários</div>', unsafe_allow_html=True)

# Cards de livros em destaque
cols_books = st.columns(3)
book_colors = ["glass-rose", "glass-gold", "glass-purple"]

for i, book in enumerate(FALLBACK_BOOKS):
    with cols_books[i]:
        st.markdown(f"""
        <div class="glass-card {book_colors[i]} book-card" style="min-height: 140px;">
            <div style="position: absolute; top: 1rem; right: 1rem;">
                <span class="badge badge-category">📖 {book['destaque']}</span>
            </div>
            <div class="card-label" style="margin-top: 0.5rem;">{book['genero']}</div>
            <div class="card-value card-value-sm" style="margin-top: 0.5rem; font-size: 1.2rem;">{book['titulo']}</div>
            <div class="card-subtitle" style="margin-top: 0.5rem;">por {book['autor']}</div>
        </div>
        """, unsafe_allow_html=True)

# Notícias sobre Livros
st.markdown("#### 📖 Notícias do Mundo Literário")

col_book_news = st.columns(1)[0]
with col_book_news:
    news_books = get_news_by_topic("lançamentos livros best-sellers literatura", max_results=6, days=14)
    if news_books:
        cols = st.columns(2)
        for idx, item in enumerate(news_books[:6]):
            with cols[idx % 2]:
                titulo = item.title[:100] + "..." if len(item.title) > 100 else item.title
                st.markdown(f"""
                <div class="news-item book-card" style="margin-bottom: 1rem;">
                    <a href="{item.link}" target="_blank">{titulo}</a>
                    <div class="news-meta">📚 Literatura · {item.get('published', 'Agora')[:16]}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma notícia recente sobre lançamentos literários")

# ═══════════════════════════════════════════════════════════════
# DICAS DO DIA (CATEGORIA ALEATÓRIA)
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-title"><span class="section-icon">💡</span> Dica do Dia</div>', unsafe_allow_html=True)

dicas = [
    {"cat": "🎬 Filme", "texto": "Assista 'Everything Everywhere All at Once' - um dos filmes mais criativos dos últimos anos disponível no Prime Video."},
    {"cat": "📺 Série", "texto": "Não perca 'The Bear' no Star+ - drama culinário intenso e aclamado pela crítica."},
    {"cat": "🎮 Jogo", "texto": "Experimente 'Hades' se gosta de jogos rogue-like com história envolvente - disponível em todas as plataformas."},
    {"cat": "📚 Livro", "texto": "Leia 'Projeto Hail Mary' de Andy Weir - ficção científica inteligente do autor de 'Perdido em Marte'."},
]

dica_hoje = random.choice(dicas)

st.markdown(f"""
<div class="glass-card glass-dark" style="text-align: center; padding: 2rem;">
    <div class="card-label" style="justify-content: center; font-size: 1rem; margin-bottom: 1rem;">{dica_hoje['cat']}</div>
    <div style="font-size: 1.2rem; color: rgba(255,255,255,0.9); font-family: 'Outfit', sans-serif; line-height: 1.6;">
        {dica_hoje['texto']}
    </div>
</div>
""", unsafe_allow_html=True)

# Botão de atualização
st.markdown("<br>", unsafe_allow_html=True)
col_btn = st.columns([1, 2, 1])
with col_btn[1]:
    if st.button("🔄 Atizar Dashboard de Entretenimento", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Footer
st.markdown(f"""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: rgba(255,255,255,0.3); font-size: 0.75rem; border-top: 1px solid rgba(255,255,255,0.1);">
    <div style="margin-bottom: 0.5rem;">Pop Culture Hub · Atualizado às {agora.strftime("%H:%M")}</div>
    <div>Fontes: TMDB · Google News · Yahoo Entertainment</div>
    <div style="margin-top: 0.5rem; font-size: 0.7rem;">
        💡 Dica: Adicione sua chave da API TMDB para recomendações personalizadas de filmes e séries
    </div>
</div>
""", unsafe_allow_html=True)
