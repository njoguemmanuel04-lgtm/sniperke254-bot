from flask import Flask, request
import os, requests
import yfinance as yf

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

def send_msg(chat_id, text):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except: pass

def gold_signal():
    try:
        data = yf.download("GC=F", period="1d", interval="15m", progress=False)
        if data.empty:
            return "⚠️ Gold data loading, try again in 10s"
        price = float(data['Close'].iloc[-1])
        tp = price + 8
        sl = price - 5
        return f"🥇 *SNIPER KE 254 - GOLD*\n\nPrice: ${price:.2f}\nSignal: *BUY GOLD* 📈\n\nTP1: ${tp:.2f}\nSL: ${sl:.2f}\n\n_Risk 1% per trade_"
    except Exception as e:
        return f"Loading... try /gold again. {e}"

@app.route('/')
def home():
    return "Sniper Bot Running"

@app.route('/api', methods=['GET'])
def check():
    return "Sniper API Ready"

@app.route('/api', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text","")
            if "/start" in text:
                send_msg(chat_id, "🔥 *Sniper Bot KE 254 LIVE!*\n\nCommands:\n/gold - Gold signal\n\nGood luck!")
            elif "gold" in text.lower():
                send_msg(chat_id, gold_signal())
            else:
                send_msg(chat_id, "Send /gold for signal")
        return "ok"
    except:
        return "ok"
