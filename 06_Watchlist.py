import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Watchlist", layout="centered")
DATA_FILE = "watchlist.csv"

# --- INITIALISIERUNG ---
def init_app():
    if 'watchlist' not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_csv(DATA_FILE)
                st.session_state.watchlist = df.to_dict('records')
            except:
                st.session_state.watchlist = []
        else:
            st.session_state.watchlist = []

init_app()

def save_watchlist():
    pd.DataFrame(st.session_state.watchlist).to_csv(DATA_FILE, index=False)

def get_market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # Historie für Vergleich
        hist = ticker.history(period="5d")
        if hist.empty: return None, None
        
        current = hist['Close'].iloc[-1]
        # Letzter Freitag oder letzter bekannter Handelstag
        friday_data = hist[hist.index.dayofweek == 4]
        friday_price = friday_data['Close'].iloc[-1] if not friday_data.empty else hist['Close'].iloc[0]
        
        return current, friday_price
    except:
        return None, None

# --- UI ---
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfekter Trade")

# Hinzufügen
with st.expander("Neues Wertpapier hinzufügen"):
    new_ticker = st.text_input("Ticker-Symbol eingeben:").upper()
    typ = st.radio("Ausrichtung:", ["Long", "Short"], horizontal=True)
    if st.button("Hinzufügen"):
        if new_ticker:
            ticker = yf.Ticker(new_ticker)
            if 'longName' in ticker.info:
                st.session_state.watchlist.append({
                    "Symbol": new_ticker, 
                    "Name": ticker.info['longName'], 
                    "Typ": typ
                })
                save_watchlist()
                st.rerun()
            else:
                st.error("Ticker nicht gefunden.")

# Anzeige als Tabelle
if st.session_state.watchlist:
    data_list = []
    for item in st.session_state.watchlist:
        curr, fri = get_market_data(item['Symbol'])
        if curr and fri:
            diff_pct = (curr - fri) / fri
            alert = f"{diff_pct:.1%}" if (item.get('Typ') == "Long" and diff_pct < -0.005) or (item.get('Typ') == "Short" and diff_pct > 0.005) else "-"
            
            data_list.append({
                "Symbol": f"{'🟢' if item['Typ'] == 'Long' else '🔴'} {item['Symbol']}",
                "Aktuell": curr,
                "Freitag": fri,
                "Alarm": alert
            })

    # Hier scrollt nur die Tabelle, der Rest der Seite bleibt stabil
    st.dataframe(
        pd.DataFrame(data_list),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Aktuell": st.column_config.NumberColumn(format="%.2f"),
            "Freitag": st.column_config.NumberColumn(format="%.2f")
        }
    )
    
    # Lösch-Funktion unter der Tabelle
    st.divider()
    del_symbol = st.selectbox("Symbol zum Löschen wählen:", [x['Symbol'] for x in st.session_state.watchlist])
    if st.button("Ausgewähltes Symbol entfernen"):
        st.session_state.watchlist = [x for x in st.session_state.watchlist if x['Symbol'] != del_symbol]
        save_watchlist()
        st.rerun()
else:
    st.info("Deine Watchlist ist leer.")
