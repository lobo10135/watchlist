import os
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA_FILE = "watchlist.csv"

def send_email_alert(subject, body):
    try:
        sender = os.environ.get("EMAIL_SENDER")
        password = os.environ.get("EMAIL_PASSWORD")
        receiver = os.environ.get("EMAIL_RECEIVER")
        
        if not sender or not password or not receiver:
            print("E-Mail-Zugangsdaten fehlen in den Environment-Variablen.")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("E-Mail erfolgreich gesendet.")
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False

def check_watchlist():
    if not os.path.exists(DATA_FILE):
        print("Keine watchlist.csv gefunden.")
        return

    df = pd.read_csv(DATA_FILE)
    if df.empty:
        print("Watchlist ist leer.")
        return

    watchlist = df.to_dict('records')
    alarms_triggered = []

    for item in watchlist:
        symbol = item['Symbol']
        typ = item['Typ']
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="20d", interval="1d")
            trading_days = hist[hist.index.dayofweek < 5]
            
            weeks = trading_days.groupby(trading_days.index.isocalendar().week)
            if len(weeks) < 2: continue
            
            completed_weeks = [w for w in weeks.groups.keys()]
            current_day = pd.Timestamp.now().dayofweek
            if current_day == 6:
                last_week_data = weeks.get_group(completed_weeks[-1])
            else:
                last_week_data = weeks.get_group(completed_weeks[-2])
            
            weekly_low = last_week_data['Low'].min()
            weekly_high = last_week_data['High'].max()
            
            hist_intraday = ticker.history(period="1d", interval="5m")
            if hist_intraday.empty: continue
            current = hist_intraday['Close'].iloc[-1]
            
            if typ == "Long":
                ref_price = weekly_low
                trigger_limit = ref_price * 0.995
                war_unter = (hist_intraday['Low'] < trigger_limit).any()
                alarm2 = True if war_unter and current >= ref_price else False
            else:
                ref_price = weekly_high
                trigger_limit = ref_price * 1.005
                war_ueber = (hist_intraday['High'] > trigger_limit).any()
                alarm2 = True if war_ueber and current <= ref_price else False
            
            if alarm2:
                alarms_triggered.append(f"Symbol: {symbol} ({typ}) - Aktuell: {current:.2f} - Ref-Preis: {ref_price:.2f}")
        except Exception as e:
            print(f"Fehler bei {symbol}: {e}")

    if alarms_triggered:
        body = "Folgende Alarme wurden im Hintergrund ausgelöst:\n\n" + "\n".join(alarms_triggered)
        send_email_alert("🚨 Viper Watchlist Automatischer Alarm!", body)
    else:
        print("Keine Alarme ausgelöst.")

if __name__ == "__main__":
    check_watchlist()
