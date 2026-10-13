import os
import json
import websocket
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
    """Helper function to send messages back to Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def check_market_session():
    """
    Checks East Africa Time (EAT = UTC+3) to detect low-liquidity hours.
    Asian / Rollover Session: 00:00 - 09:00 EAT
    """
    eat_tz = timezone(timedelta(hours=3))
    now_eat = datetime.now(eat_tz)
    hour = now_eat.hour

    if 0 <= hour < 9:
        return (
            "⚠️ *SESSION WARNING:* Low-Liquidity Asian Session (00:00 - 09:00 EAT).\n"
            " Broker spreads are wider and fakeouts are common. Trade with caution or wait for London/NY sessions!\n\n"
        )
    return ""

def get_live_gold_price():
    try:
        url = "https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT"
        res = requests.get(url, timeout=5).json()
        return float(res["symbols"][0]["price"])
    except Exception:
        return None

def get_live_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = requests.get(url, timeout=5).json()
        return float(res["bitcoin"]["usd"])
    except Exception:
        return None

def get_forex_rates():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        res = requests.get(url, timeout=5).json()
        rates = res.get("rates", {})
        eur_usd = 1.0 / rates["EUR"] if "EUR" in rates else None
        usd_jpy = rates.get("JPY")
        return eur_usd, usd_jpy
    except Exception:
        return None, None

def get_deriv_price(symbol="R_75"):
    """Fetches live tick price from Deriv WebSocket API (App ID: 59828)"""
    try:
        ws_url = "wss://ws.derivws.com/websockets/v3?app_id=59828"
        ws = websocket.create_connection(ws_url, timeout=3)
        ws.send(json.dumps({"ticks": symbol}))
        response = json.loads(ws.recv())
        ws.close()
        if "tick" in response:
            return float(response["tick"]["quote"])
    except Exception:
        pass
    return None

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").upper()
        
        session_warning = check_market_session()

        if "/START" in text or "START" in text:
            reply = (
                "🔥 *SNIPER KE 254 BOT LIVE!* 🔥\n\n"
                "Commands:\n"
                "/gold - Dynamic Gold Signal\n"
                "/btc - Dynamic Bitcoin Signal\n"
                "/forex - Dynamic Forex Signals\n"
                "/deriv - Deriv Volatility Indices (V75 & V100)"
            )
            send_message(chat_id, reply)

        elif "/GOLD" in text:
            price = get_live_gold_price()
            if price:
                sl = price - 25.0
                tp1 = price + 35.0
                tp2 = price + 70.0
                
                reply = (
                    f"🥇 *SNIPER KE 254 - GOLD (XAU/USD)*\n\n"
                    f"{session_warning}"
                    f"📍 *Entry (Live):* ${price:,.2f}\n"
                    f"📈 *Signal:* BUY GOLD\n\n"
                    f"🎯 *TP1:* ${tp1:,.2f}\n"
                    f"🎯 *TP2:* ${tp2:,.2f}\n"
                    f"🛑 *SL:* ${sl:,.2f}\n\n"
                    f"⚖️ *Risk:* 1% per trade"
                )
            else:
                reply = "⚠️ *Error:* Live Gold data currently unavailable."
            send_message(chat_id, reply)

        elif "/BTC" in text:
            price = get_live_btc_price()
            if price:
                sl = price - 800.0
                tp1 = price + 1200.0
                tp2 = price + 2500.0
                
                reply = (
                    f"₿ *SNIPER KE 254 - BITCOIN (BTC/USD)*\n\n"
                    f"{session_warning}"
                    f"📍 *Entry (Live):* ${price:,.2f}\n"
                    f"🚀 *Signal:* BUY BITCOIN\n\n"
                    f"🎯 *TP1:* ${tp1:,.2f}\n"
                    f"🎯 *TP2:* ${tp2:,.2f}\n"
                    f"🛑 *SL:* ${sl:,.2f}\n\n"
                    f"⚖️ *Risk:* 1-2% per trade"
                )
            else:
                reply = "⚠️ *Error:* Live Bitcoin data currently unavailable."
            send_message(chat_id, reply)

        elif "/FOREX" in text:
            eur_usd, usd_jpy = get_forex_rates()
            if eur_usd and usd_jpy:
                eur_sl = eur_usd - 0.0030
                eur_tp = eur_usd + 0.0050
                jpy_sl = usd_jpy + 0.30
                jpy_tp = usd_jpy - 0.50
                
                reply = (
                    f"💱 *SNIPER KE 254 - LIVE FOREX SIGNALS*\n\n"
                    f"{session_warning}"
                    f"🟢 *EUR/USD - BUY*\n"
                    f"Entry: `{eur_usd:.5f}`\n"
                    f"🎯 TP: `{eur_tp:.5f}` | 🛑 SL: `{eur_sl:.5f}`\n\n"
                    f"🔴 *USD/JPY - SELL*\n"
                    f"Entry: `{usd_jpy:.3f}`\n"
                    f"🎯 TP: `{jpy_tp:.3f}` | 🛑 SL: `{jpy_sl:.3f}`"
                )
            else:
                reply = "⚠️ *Error:* Live Forex data currently unavailable."
            send_message(chat_id, reply)

        elif "/DERIV" in text or "/VOLATILITY" in text:
            v75_price = get_deriv_price("R_75")
            v100_price = get_deriv_price("R_100")
            
            if v75_price and v100_price:
                v75_sl = v75_price * 0.995
                v75_tp = v75_price * 1.010
                v100_sl = v100_price * 0.995
                v100_tp = v100_price * 1.010
                
                reply = (
                    f"📊 *SNIPER KE 254 - DERIV SYNTHETICS*\n\n"
                    f"📉 *VOLATILITY 75 INDEX - BUY*\n"
                    f"Entry: `{v75_price:,.2f}`\n"
                    f"🎯 TP: `{v75_tp:,.2f}` | 🛑 SL: `{v75_sl:,.2f}`\n\n"
                    f"📈 *VOLATILITY 100 INDEX - BUY*\n"
                    f"Entry: `{v100_price:,.2f}`\n"
                    f"🎯 TP: `{v100_tp:,.2f}` | 🛑 SL: `{v100_sl:,.2f}`\n\n"
                    f"⚖️ *Risk:* $1.00 Multiplier Stake"
                )
            else:
                reply = "⚠️ *Error:* Deriv WebSocket connection timed out."
            send_message(chat_id, reply)
            
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    return "🔥 SNIPER KE 254 LIVE!"

if __name__ == "__main__":
    app.run(debug=True)
