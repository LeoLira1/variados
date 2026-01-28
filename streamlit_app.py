import streamlit as st
import yfinance as yf
import requests
import feedparser
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Meu Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Meu Dashboard Pessoal")
st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Criar colunas
col1, col2 = st.columns(2)

# === CLIMA - QUIRINÓPOLIS ===
with col1:
    st.subheader("🌤️ Clima em Quirinópolis - GO")
    try:
        clima_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": -18.4486,
                "longitude": -50.4519,
                "current_weather": True,
                "timezone": "America/Sao_Paulo"
            },
            timeout=10
        )
        clima = clima_resp.json().get("current_weather", {})
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Temperatura", f"{clima.get('temperature', '?')}°C")
        c2.metric("💨 Vento", f"{clima.get('windspeed', '?')} km/h")
        c3.metric("🧭 Direção", f"{clima.get('winddirection', '?')}°")
    except Exception as e:
        st.error(f"Erro ao carregar clima: {e}")

# === AÇÕES ===
with col2:
    st.subheader("📈 Ações B3")
    tickers = ["PRIO3.SA", "PETR4.SA", "VALE3.SA", "ITUB4.SA"]
    
    for ticker in tickers:
        try:
            acao = yf.Ticker(ticker)
            hist = acao.history(period="2d")
            if len(hist) >= 2:
                preco_atual = hist['Close'].iloc[-1]
                preco_anterior = hist['Close'].iloc[-2]
                variacao = ((preco_atual - preco_anterior) / preco_anterior) * 100
                st.metric(
                    ticker.replace(".SA", ""),
                    f"R$ {preco_atual:.2f}",
                    f"{variacao:+.2f}%"
                )
            elif len(hist) == 1:
                preco_atual = hist['Close'].iloc[-1]
                st.metric(ticker.replace(".SA", ""), f"R$ {preco_atual:.2f}")
        except Exception as e:
            st.metric(ticker.replace(".SA", ""), "Erro")

# === NOTÍCIAS ===
st.subheader("📰 Notícias")

col_news1, col_news2 = st.columns(2)

with col_news1:
    st.markdown("**Coruripe - AL**")
    try:
        feed_coruripe = feedparser.parse(
            "https://news.google.com/rss/search?q=Coruripe+Alagoas&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )
        for entry in feed_coruripe.entries[:5]:
            st.markdown(f"• [{entry.title}]({entry.link})")
    except:
        st.warning("Não foi possível carregar notícias de Coruripe")

with col_news2:
    st.markdown("**Quirinópolis - GO**")
    try:
        feed_quiri = feedparser.parse(
            "https://news.google.com/rss/search?q=Quirinópolis+Goiás&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )
        for entry in feed_quiri.entries[:5]:
            st.markdown(f"• [{entry.title}]({entry.link})")
    except:
        st.warning("Não foi possível carregar notícias de Quirinópolis")

# Botão de atualização
st.button("🔄 Atualizar dados")
