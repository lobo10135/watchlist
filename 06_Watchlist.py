import streamlit as st
import yfinance as yf
import pandas as pd
import os

# Konfiguration
st.set_page_config(page_title="Viper Watchlist", layout="centered")
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
        hist = ticker.history(period="5d")
        if hist.empty: return None, None
        
        current = hist['Close'].iloc[-1]
        friday_data = hist[hist.index.dayofweek == 4]
        friday_price = friday_data['Close'].iloc[-1] if not friday_data.empty else hist['Close'].iloc[0]
        
        return current, friday_price
    except:
        return None, None

# --- UI ---
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfect Trade")
st.write("") # Leerzeile unter der Überschrift

# Hinzufügen-Logik mit Duplikat-Prüfung
with st.expander("➕ Neues Wertpapier hinzufügen"):
    st.write("") # Leerzeile unter dem Expander-Text
    new_ticker = st.text_input("Ticker-Symbol:", placeholder="z.B. AAPL").upper()
    typ = st.radio("Ausrichtung:", ["Long", "Short"], horizontal=True)
    
    if st.button("Zur Watchlist hinzufügen"):
        if not new_ticker:
            st.warning("Bitte gib ein Ticker-Symbol ein.")
        # Prüfung: Ist das Symbol schon in der Liste vorhanden?
        elif any(item['Symbol'] == new_ticker for item in st.session_state.watchlist):
            st.error(f"Das Symbol {new_ticker} ist bereits in der Watchlist enthalten.")
        else:
            ticker = yf.Ticker(new_ticker)
            try:
                info = ticker.info
                if 'longName' in info:
                    st.session_state.watchlist.append({
                        "Symbol": new_ticker, 
                        "Name": info['longName'], 
                        "Typ": typ
                    })
                    save_watchlist()
                    st.rerun()
                else:
                    st.error("Ticker konnte nicht gefunden werden.")
            except Exception:
                st.error("Fehler beim Abrufen der Ticker-Daten.")

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

    # Scrollbare Tabelle für Mobilgeräte
    st.dataframe(
        pd.DataFrame(data_list),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Aktuell": st.column_config.NumberColumn(format="%.2f"),
            "Freitag": st.column_config.NumberColumn(format="%.2f"),
            "Alarm": st.column_config.TextColumn("Alarm", width="small")
        }
    )
    
    st.divider()
    # Löschen über Auswahlmenü
    options = {f"{x['Symbol']} - {x['Name']}": x['Symbol'] for x in st.session_state.watchlist}
    del_selection = st.selectbox("Symbol zum Löschen auswählen:", options=options.keys())
    
    if st.button("Ausgewähltes Symbol entfernen"):
        target = options[del_selection]
        st.session_state.watchlist = [x for x in st.session_state.watchlist if x['Symbol'] != target]
        save_watchlist()
        st.rerun()
else:
    st.info("Deine Watchlist ist aktuell leer.")
