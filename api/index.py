from flask import Flask, request
import os, requests
app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

def send(cid, txt):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "Markdown"}, timeout=10)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return "🔥 SNIPER KE 254 LIVE!"
    data = request.get_json(force=True, silent=True) or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        t = data["message"].get("text","").upper()
        if "/START" in t:
            send(chat_id, "🔥 *SNIPER KE 254 BOT LIVE!* 🔥\n\n/gold\n/btc\n/forex")
            return "ok"
        if "/FOREX" in t:
            send(chat_id, "💱 FOREX LIVE - 7 MAJORS")
            return "ok"
        if "GOLD" in t:
            send(chat_id, "🥇 GOLD $2650 BUY")
            return "ok"
    return "ok"
