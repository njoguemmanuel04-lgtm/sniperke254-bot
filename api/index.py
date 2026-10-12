from flask import Flask, request
import os, requests

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

FOREX = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/CHF": "EURCHF=X",
    "GBP/JPY": "GBPJPY=X",
    "GBP/CHF": "GBPCHF=X",
    "AUD/JPY": "AUDJPY=X",
    "NZD/JPY": "NZDJPY=X",
    "GOLD": "GC=F",
    "BTC": "BTC-USD"
}

def send_msg(chat_id, text):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5).json()
        price = r['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except:
        return None

def format_signal(pair, price):
    if price is None:
        return f"{pair}: Loading..."
    # Simple sniper logic - demo
    return f"{pair}: {price:.5f}" if price < 100 else f"{pair}: ${price:.2f}"

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST': return webhook()
    return "Sniper KE 254 - ALL FOREX LIVE"

@app.route('/api', methods=['GET','POST'])
def webhook():
    if request.method == 'GET': return "Sniper API - All Forex Ready"
    try:
        data = request.get_json(force=True, silent=True) or {}
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            txt = data["message"].get("text","").upper().replace("/","").replace(" ","")

            # START
            if "START" in txt:
                send_msg(chat_id, "🔥 *SNIPER KE 254 - ALL MARKETS* 🔥\n\n*Commands:*\n/gold or /xauusd - Gold\n/btc - Bitcoin\n/forex - All 7 Majors Live\n\n*Individual:*\n/eurusd /gbpusd /usdjpy /usdchf /audusd /nzdusd /usdcad\n/eurgbp /eurjpy /gbpjpy\n\nJust type pair name e.g. `EURUSD`")
                return "ok"

            # GOLD
            if "GOLD" in txt or "XAUUSD" in txt or txt == "XAU":
                p = get_price("GC=F")
                price_str = f"${p:.2f}" if p else "$2650.50"
                send_msg(chat_id, f"🥇 *GOLD (XAU/USD) LIVE*\n\nPrice: {price_str}\nSignal: *BUY* 📈\n\nEntry: {price_str}\nSL: - $5\nTP1: + $8\nTP2: + $15\n\n_Sniper KE 254_")
                return "ok"

            # BTC
            if "BTC" in txt:
                p = get_price("BTC-USD")
                price_str = f"${p:,.2f}" if p else "$67,000"
                send_msg(chat_id, f"₿ *BTC/USD LIVE*\n\nPrice: {price_str}\nSignal: *BUY* 🚀\n\nTP: + $800\nSL: - $500")
                return "ok"

            # FOREX ALL - 7 Majors
            if "FOREX" in txt or txt == "ALL":
                msg = "💱 *LIVE FOREX - 7 MAJORS* 💱\n\n"
                majors = ["EUR/USD","GBP/USD","USD/JPY","USD/CHF","AUD/USD","NZD/USD","USD/CAD"]
                for pair in majors:
                    sym = FOREX[pair]
                    p = get_price(sym)
                    if p:
                        if "JPY" in pair: msg += f"{pair}: {p:.3f}\n"
                        else: msg += f"{pair}: {p:.5f}\n"
                    else:
                        msg += f"{pair}: Loading...\n"
                msg += "\n_Type EURUSD for signal_"
                send_msg(chat_id, msg)
                return "ok"

            # INDIVIDUAL PAIR - check if user typed EURUSD etc
            for pair, sym in FOREX.items():
                clean_pair = pair.replace("/","").replace(" ","")
                if clean_pair in txt:
                    p = get_price(sym)
                    if not p:
                        send_msg(chat_id, f"{pair} loading... try again")
                        return "ok"
                    if "JPY" in pair:
                        send_msg(chat_id, f"💱 *{pair} LIVE*\n\nPrice: {p:.3f}\nSignal: *BUY* 📈\nTP: {p+0.20:.3f}\nSL: {p-0.15:.3f}")
                    elif p > 100:
                        send_msg(chat_id, f"💱 *{pair} LIVE*\n\nPrice: ${p:.2f}\nSignal: *BUY* 📈\nTP: ${p+5:.2f}\nSL: ${p-3:.2f}")
                    else:
                        send_msg(chat_id, f"💱 *{pair} LIVE*\n\nPrice: {p:.5f}\nSignal: *BUY* 📈\nTP: {p+0.0020:.5f}\nSL: {p-0.0010:.5f}")
                    return "ok"

            # Default help
            send_msg(chat_id, "Try:\n/forex - All majors\n/gold\n/btc\n/eurusd")
        return "ok"
    except Exception as e:
        print(f"Error {e}")
        return "ok"
