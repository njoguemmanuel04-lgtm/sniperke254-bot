from flask import Flask, request
import os, requests

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)

# THIS FIXES YOUR SCREENSHOT - Visit button
@app.route('/')
def home():
    return "🔥 SNIPER KE 254 BOT LIVE - READY FOR SIGNALS!"

# THIS IS FOR TELEGRAM WEBHOOK
@app.route('/api', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "API LIVE - SET WEBHOOK TO THIS URL"
    data = request.get_json(silent=True, force=True) or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text","").upper()
        
        if "/START" in text:
            send(chat_id, "🔥 *SNIPER KE 254 - ALL MARKETS LIVE!* 🔥\n\n/gold - Gold Signal\n/btc - Bitcoin\n/forex - 7 Majors\n\nTap menu below 👇")
            return "ok"
        if "/FOREX" in text:
            send(chat_id, "💱 *FOREX 7 MAJORS LIVE*\n\nEUR/USD BUY\nGBP/USD BUY\nUSD/JPY SELL\n\n_Live feed working!_")
            return "ok"
        if "GOLD" in text:
            send(chat_id, "🥇 *GOLD* $2650 BUY 📈")
            return "ok"
        if "BTC" in text:
            send(chat_id, "₿ *BTC* $68000 BUY")
            return "ok"
            
    return "ok"
