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
        # 20 Tage laden, um sicher die letzte volle Handelswoche zu erhalten
        hist = ticker.history(period="20d", interval="1d")
        
        # Nur Wochentage (Mo-Fr) berücksichtigen
        trading_days = hist[hist.index.dayofweek < 5]
        
        # Gruppierung nach Kalenderwoche und Filterung auf die letzte Woche mit 5 Tagen
        weeks = trading_days.groupby(trading_days.index.isocalendar().week)
        # Wir wählen die vorletzte Woche, falls die aktuelle Woche noch läuft
        # oder die letzte, falls heute Sonntag ist (die Woche ist abgeschlossen)
        if len(weeks) < 2: return None, None, None, None
        
        # Index der abgeschlossenen Wochen
        completed_weeks = [w for w in weeks.groups.keys()]
        # Wenn heute Sonntag ist (dayofweek 6), ist die aktuelle Woche abgeschlossen.
        # Ansonsten nehmen wir die vorherige.
        current_day = pd.Timestamp.now().dayofweek
        if current_day == 6:
            last_week_data = weeks.get_group(completed_weeks[-1])
        else:
            last_week_data = weeks.get_group(completed_weeks[-2])
        
        weekly_low = last_week_data['Low'].min()
        weekly_high = last_week_data['High'].max()
        
        # Aktueller Kurs für die Alarmprüfung
        hist_intraday = ticker.history(period="1d", interval="5m")
        if hist_intraday.empty: return None, None, None, None
        current = hist_intraday['Close'].iloc[-1]
        
        return current, weekly_low, weekly_high, hist_intraday
    except:
        return None, None, None, None

# --- UI ---
if os.path.exists("bulle.jpg"):
    st.image("bulle.jpg", use_container_width=True)

st.subheader("🐂 Watchlist perfect Trade")

with st.expander("➕ Symbol hinzufügen (Infos)"):
    st.info("• Deutsche Aktien: Bitte '.DE' am Ende anhängen (z.B. SAP.DE)\n• Gold: 'GC=F'\n• WTI Öl: 'CL=F'")
    new_ticker = st.text_input("Ticker-Symbol:", placeholder="z.B. SAP.DE oder GC=F").upper()
    typ = st.radio("Ausrichtung:", ["Long", "Short"], horizontal=True)
    
    if st.button("Symbol hinzufügen"):
        if not new_ticker:
            st.warning("Bitte gib ein Ticker-Symbol ein.")
        elif any(item['Symbol'] == new_ticker for item in st.session_state.watchlist):
            st.error(f"Das Symbol {new_ticker} ist bereits enthalten.")
        else:
            ticker = yf.Ticker(new_ticker)
            try:
                data = ticker.history(period="1d")
                if not data.empty:
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
        curr, weekly_low, weekly_high, hist_intraday = get_analysis_data(item['Symbol'])
        
        if curr is not None:
            if item['Typ'] == "Long":
                ref_price = weekly_low
                diff_pct = (curr - ref_price) / ref_price
                alert = f"🔥 {diff_pct:.2%}" if diff_pct <= -0.005 else "-"
                
                trigger_limit = ref_price * 0.995
                war_unter = (hist_intraday['Low'] < trigger_limit).any()
                alarm2 = "🔥" if war_unter and curr >= ref_price else "-"
                
            else: # Short
                ref_price = weekly_high
                diff_pct = (curr - ref_price) / ref_price
                alert = f"🔥 {diff_pct:.2%}" if diff_pct >= 0.005 else "-"
                
                trigger_limit = ref_price * 1.005
                war_ueber = (hist_intraday['High'] > trigger_limit).any()
                alarm2 = "🔥" if war_ueber and curr <= ref_price else "-"
            
            data_list.append({
                "Symbol": f"{'🟢' if item['Typ'] == 'Long' else '🔴'} {item['Symbol']}",
                "Aktuell": curr,
                "Weekly high / low": ref_price,
                "Alarm": alert,
                "Alarm 2": alarm2
            })

    st.dataframe(pd.DataFrame(data_list), use_container_width=True, hide_index=True)
    
    st.divider()
    options = {f"{x['Symbol']} ({x['Typ']})": x['Symbol'] for x in st.session_state.watchlist}
    del_selection = st.selectbox("Symbol zum Löschen auswählen:", options=options.keys())
    
    if st.button("Symbol entfernen"):
        target = options[del_selection]
        st.session_state.watchlist = [x for x in st.session_state.watchlist if x['Symbol'] != target]
        save_watchlist()
        st.rerun()
else:
    st.info("Deine Watchlist ist aktuell leer.")
