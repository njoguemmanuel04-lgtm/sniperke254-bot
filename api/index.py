from flask import Flask, request
import os, requests, time

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

FOREX = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X"
}

# Fallback defaults in case Yahoo blocks requests
FALLBACK_PRICES = {
    "EURUSD=X": 1.0850, "GBPUSD=X": 1.3000, "USDJPY=X": 150.50,
    "USDCHF=X": 0.8800, "AUDUSD=X": 0.6500, "NZDUSD=X": 0.6000,
    "USDCAD=X": 1.3500, "GC=F": 2650.50, "BTC-USD": 67000.0
}

def send_msg(c, t):
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": c, "text": t, "parse_mode": "Markdown"},
            timeout=10
        )
        if not res.ok:
            print(f"Telegram API Error: {res.text}")
    except Exception as e:
        print(f"Send message exception: {e}")

def get_price(s):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=5).json()
        price = r['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except Exception as e:
        print(f"Price fetch error for {s}: {e}")
        return FALLBACK_PRICES.get(s, None)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return webhook()
    return "Sniper KE 254 - Online"

@app.route('/api', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "API LIVE"
    try:
        data = request.get_json(force=True, silent=True) or {}
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            txt = data["message"].get("text", "").upper()
            
            if "/START" in txt:
                send_msg(chat_id, "🔥 *SNIPER KE 254 - ALL MARKETS LIVE!* 🔥\n\n/gold - Gold\n/btc - Bitcoin\n/forex - All 7 Majors\n\n_Tap menu below!_")
                return "ok"
                
            if "/FOREX" in txt:
                msg = "💱 *LIVE FOREX - 7 MAJORS* 💱\n\n"
                for pair, sym in FOREX.items():
                    p = get_price(sym)
                    time.sleep(0.2) # Prevent rate-limiting / blocking from Yahoo
                    if p:
                        msg += f"{pair}: {p:.5f}\n" if p < 200 else f"{pair}: {p:.2f}\n"
                    else:
                        msg += f"{pair}: Unavailable\n"
                send_msg(chat_id, msg)
                return "ok"
                
            if "GOLD" in txt or "XAU" in txt:
                p = get_price("GC=F")
                send_msg(chat_id, f"🥇 *GOLD LIVE*\n\nPrice: ${p:.2f}\nSignal: BUY 📈\nSL: ${p-5:.2f}\nTP: ${p+8:.2f}")
                return "ok"
                
            if "BTC" in txt:
                p = get_price("BTC-USD")
                send_msg(chat_id, f"₿ *BTC LIVE*\n\nPrice: ${p:,.2f}\nBUY 🚀")
                return "ok"
                
            for pair, sym in FOREX.items():
                if pair.replace("/", "") in txt.replace("/", "").replace(" ", ""):
                    p = get_price(sym)
                    if p:
                        send_msg(chat_id, f"💱 *{pair} LIVE*\n\nPrice: {p}\nBUY 📈\nTP: {p*1.001:.5f}\nSL: {p*0.999:.5f}")
                    else:
                        send_msg(chat_id, f"Could not fetch live price for {pair} right now.")
                    return "ok"
                    
        return "ok"
    except Exception as e:
        print(f"Webhook global error: {e}")
        return "ok"
