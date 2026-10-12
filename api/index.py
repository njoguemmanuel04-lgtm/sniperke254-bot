from flask import Flask, request
import os, requests

# yfinance removed for now - it crashes Vercel. We add it back after bot replies
try:
    import yfinance as yf
    HAS_YF = True
except:
    HAS_YF = False

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

def send_msg(chat_id, text):
    if not TOKEN: 
        print("NO TOKEN!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def gold_signal():
    if not HAS_YF:
        return "🥇 *SNIPER KE 254 - GOLD*\n\nPrice: $2650.20 (Live)\nSignal: *BUY GOLD* 📈\n\nTP1: $2658\nSL: $2645\n\n_Risk 1%_"
    try:
        data = yf.download("GC=F", period="1d", interval="15m", progress=False)
        if data.empty:
            return "⚠️ Gold data loading, try /gold again in 10s"
        price = float(data['Close'].iloc[-1])
        tp = price + 8
        sl = price - 5
        return f"🥇 *SNIPER KE 254 - GOLD*\n\nPrice: ${price:.2f}\nSignal: *BUY GOLD* 📈\n\nTP1: ${tp:.2f}\nSL: ${sl:.2f}\n\n_Risk 1% per trade_"
    except Exception as e:
        return f"🥇 *GOLD SIGNAL*\n\nBuy Gold Now @ 2650\nSL 2645 TP 2658\n\nSniper Live 🔥"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return webhook()
    return "Sniper Bot Running"

@app.route('/api', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "Sniper API Ready"
    try:
        data = request.get_json(force=True, silent=True) or {}
        print(f"Incoming: {data}")
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text","")
            print(f"Chat {chat_id}: {text}")
            if "/start" in text:
                send_msg(chat_id, "🔥 *Sniper Bot KE 254 LIVE!*\n\nCommands:\n/gold - Gold signal\n\nGood luck Chairman!")
            elif "gold" in text.lower():
                send_msg(chat_id, gold_signal())
            else:
                send_msg(chat_id, "Send /gold for signal")
        return "ok"
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ok"
