import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_FILE = "watchlist.csv"

# --- SICHERE INITIALISIERUNG ---
def init_app():
    if 'watchlist' not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_csv(DATA_FILE)
                if 'Typ' not in df.columns: df['Typ'] = 'Long'
                st.session_state.watchlist = df.to_dict('records')
            except:
                st.session_state.watchlist = []
        else:
            st.session_state.watchlist = []
    if 'last_input' not in st.session_state:
        st.session_state.last_input = ""

init_app()

# --- FUNKTIONEN ---
def save_watchlist():
    df = pd.DataFrame(st.session_state.watchlist)
    df.to_csv(DATA_FILE, index=False)

def get_market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        current = ticker.fast_info['last_price']
        currency = ticker.fast_info['currency']
        
        today = datetime.now()
        days_since_friday = (today.weekday() - 4) % 7
        if days_since_friday == 0: days_since_friday = 7
        last_friday = today - timedelta(days=days_since_friday)
        
        hist = ticker.history(start=last_friday.strftime('%Y-%m-%d'), 
                              end=(last_friday + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        friday_price = hist['Close'].iloc[-1] if not hist.empty else None
        return current, friday_price, currency
    except:
        return None, None, ""

# --- UI ---
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfekter Trade")

with st.expander("Neues Wertpapier hinzufügen", expanded=False):
    user_input = st.text_input("Ticker-Symbol eingeben:", key="ticker_input")
    if user_input and user_input != st.session_state.last_input:
        st.session_state.last_input = user_input
        ticker = yf.Ticker(user_input.upper())
        if 'longName' in ticker.info:
            st.session_state.temp_ticker = ticker.ticker
            st.session_state.temp_name = ticker.info['longName']
            st.rerun()
        else:
            st.error("Ticker nicht gefunden.")

    if 'temp_ticker' in st.session_state:
        st.write(f"### {st.session_state.temp_name} ({st.session_state.temp_ticker})")
        typ = st.radio("Ausrichtung wählen:", ["Long", "Short"], horizontal=True)
        if st.button("Bestätigen und hinzufügen"):
            st.session_state.watchlist.append({"Symbol": st.session_state.temp_ticker, "Name": st.session_state.temp_name, "Typ": typ})
            save_watchlist()
            del st.session_state.temp_ticker; del st.session_state.temp_name; st.session_state.last_input = ""; st.rerun()

# Watchlist-Anzeige
if st.session_state.watchlist:
    # Header fest in einer Zeile erzwingen
    # Wir nehmen extrem schmale Verhältnisse, damit der Platz für eine Reihe reicht
    cols = st.columns([0.22, 0.22, 0.22, 0.17, 0.17])
    cols[0].write("**Wert**"); cols[1].write("**Aktuell**"); cols[2].write("**Fr.**"); cols[3].write("**Stat.**"); cols[4].write("")

    for i, item in enumerate(st.session_state.watchlist):
        curr, fri, curr_symbol = get_market_data(item['Symbol'])
        
        if curr and fri:
            # Hier auch die Spaltenverhältnisse für die Datenzeile
            c1, c2, c3, c4, c5 = st.columns([0.22, 0.22, 0.22, 0.17, 0.17])
            icon = "🟢" if item.get('Typ', 'Long') == "Long" else "🔴"
            
            c1.write(f"{icon} **{item['Symbol']}**")
            c2.write(f"{curr:.2f}")
            c3.write(f"{fri:.2f}")
            
            diff_pct = (curr - fri) / fri
            alert = ""
            if item.get('Typ') == "Long" and diff_pct < -0.005:
                alert = f"🔥 {diff_pct:.1%}"
            elif item.get('Typ') == "Short" and diff_pct > 0.005:
                alert = f"🔥 {diff_pct:+.1%}"
            
            c4.write(alert)
            if c5.button("Entf.", key=f"del_{i}"):
                del st.session_state.watchlist[i]
                save_watchlist()
                st.rerun()
else:
    st.info("Deine Watchlist ist leer.")
