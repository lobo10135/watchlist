import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Watchlist", layout="centered")
DATA_FILE = "watchlist.csv"

def init_app():
    if 'watchlist' not in st.session_state:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            st.session_state.watchlist = df.to_dict('records')
        else:
            st.session_state.watchlist = []

init_app()

def save_watchlist():
    pd.DataFrame(st.session_state.watchlist).to_csv(DATA_FILE, index=False)

def get_market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if hist.empty: return None, None
        curr = hist['Close'].iloc[-1]
        fri = hist[hist.index.dayofweek == 4]['Close'].iloc[-1] if not hist.empty else curr
        return curr, fri
    except: return None, None

# --- UI ---
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfekter Trade")

# Hinzufügen
with st.expander("Neues Wertpapier"):
    new_ticker = st.text_input("Ticker:").upper()
    typ = st.radio("Typ:", ["Long", "Short"], horizontal=True)
    if st.button("Hinzufügen"):
        ticker = yf.Ticker(new_ticker)
        if 'longName' in ticker.info:
            st.session_state.watchlist.append({"Symbol": new_ticker, "Name": ticker.info['longName'], "Typ": typ})
            save_watchlist()
            st.rerun()

# Tabelle als "statische" Anzeige (kein st.dataframe)
# Wir nutzen ein einfaches Grid-Layout
cols = st.columns([2, 1.5, 1.5, 1.5, 1])
cols[0].write("**Wert**"); cols[1].write("**Akt.**"); cols[2].write("**Fr.**"); cols[3].write("**Stat.**"); cols[4].write("")

for i, item in enumerate(st.session_state.watchlist):
    curr, fri = get_market_data(item['Symbol'])
    if curr and fri:
        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1.5, 1])
        icon = "🟢" if item['Typ'] == "Long" else "🔴"
        
        c1.write(f"{icon} {item['Symbol']}")
        c2.write(f"{curr:.2f}")
        c3.write(f"{fri:.2f}")
        
        diff = (curr - fri) / fri
        alert = f"🔥{diff:.1%}" if (item['Typ'] == "Long" and diff < -0.005) or (item['Typ'] == "Short" and diff > 0.005) else "-"
        c4.write(alert)
        
        if c5.button("X", key=f"del_{i}"):
            st.session_state.watchlist.pop(i)
            save_watchlist()
            st.rerun()
