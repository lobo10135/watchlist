import streamlit as st
import yfinance as yf
import pandas as pd
import os

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

@st.cache_data(ttl=300)
def get_analysis_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist_day = ticker.history(period="7d")
        if hist_day.empty: return None, None, None, None
        
        fridays = hist_day[hist_day.index.dayofweek == 4]
        fri_low = fridays['Low'].iloc[-1] if not fridays.empty else hist_day['Low'].iloc[0]
        fri_high = fridays['High'].iloc[-1] if not fridays.empty else hist_day['High'].iloc[0]
        
        hist_intraday = ticker.history(period="2d", interval="5m")
        current = hist_intraday['Close'].iloc[-1]
        
        return current, fri_low, fri_high, hist_intraday
    except:
        return None, None, None, None

# --- UI ---
# Das Bild wird hier wieder geladen
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfect Trade")

with st.expander("➕ Symbol hinzufügen (Infos)"):
    st.info("• Deutsche Aktien: Bitte '.DE' am Ende anhängen (z.B. SAP.DE)\n• Gold: 'GC=F'\n• WTI Öl: 'CL=F'")
    new_ticker = st.text_input("Ticker-Symbol:", placeholder="z.B. SAP.DE oder GC=F").upper()
    typ = st.radio("Ausrichtung:", ["Long", "Short"], horizontal=True)
    
    if st.button("Zur Watchlist hinzufügen"):
        if not new_ticker:
            st.warning("Bitte gib ein Ticker-Symbol ein.")
        elif any(item['Symbol'] == new_ticker for item in st.session_state.watchlist):
            st.error(f"Das Symbol {new_ticker} ist bereits enthalten.")
        else:
            ticker = yf.Ticker(new_ticker)
            try:
                data = ticker.history(period="1d")
                if not data.empty:
                    # Versuche Firmennamen zu laden
                    full_name = ticker.info.get('longName', new_ticker)
                    st.session_state.watchlist.append({"Symbol": new_ticker, "Name": full_name, "Typ": typ})
                    save_watchlist()
                    st.rerun()
                else:
                    st.error("Ticker konnte nicht gefunden werden.")
            except:
                st.error("Fehler beim Abrufen der Ticker-Daten.")

if st.session_state.watchlist:
    data_list = []
    for item in st.session_state.watchlist:
        curr, low_fri, high_fri, hist = get_analysis_data(item['Symbol'])
        
        if curr is not None:
            if item['Typ'] == "Long":
                ref_price = low_fri
                diff_pct = (curr - ref_price) / ref_price
                alert = f"🔥 {diff_pct:.2%}" if diff_pct < -0.005 else "-"
                trigger_limit = low_fri * 0.995
                war_unter = (hist['Low'] < trigger_limit).any()
                alarm2 = "🔥" if war_unter and curr >= low_fri else "-"
            else: 
                ref_price = high_fri
                diff_pct = (curr - ref_price) / ref_price
                alert = f"🔥 {diff_pct:.2%}" if diff_pct > 0.005 else "-"
                trigger_limit = high_fri * 1.005
                war_ueber = (hist['High'] > trigger_limit).any()
                alarm2 = "🔥" if war_ueber and curr <= high_fri else "-"
            
            data_list.append({
                "Symbol": f"{'🟢' if item['Typ'] == 'Long' else '🔴'} {item['Symbol']}",
                "Aktuell": curr,
                "Freitag": ref_price,
                "Alarm": alert,
                "Alarm 2": alarm2
            })

    st.dataframe(pd.DataFrame(data_list), use_container_width=True, hide_index=True)
    
    st.divider()
    options = {f"{x['Symbol']} ({x['Typ']})": x['Symbol'] for x in st.session_state.watchlist}
    del_selection = st.selectbox("Symbol zum Löschen auswählen:", options=options.keys())
    
    if st.button("Ausgewähltes Symbol entfernen"):
        target = options[del_selection]
        st.session_state.watchlist = [x for x in st.session_state.watchlist if x['Symbol'] != target]
        save_watchlist()
        st.rerun()
else:
    st.info("Deine Watchlist ist aktuell leer.")
