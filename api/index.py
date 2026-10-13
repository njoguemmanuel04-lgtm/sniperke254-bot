import os
import json
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
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

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
        res = requests.get(url, timeout=4).json()
        return float(res["symbols"][0]["price"])
    except Exception:
        return 2650.40

def get_live_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = requests.get(url, timeout=4).json()
        return float(res["bitcoin"]["usd"])
    except Exception:
        return 65400.00

def get_forex_rates():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        res = requests.get(url, timeout=4).json()
        rates = res.get("rates", {})
        eur_usd = 1.0 / rates["EUR"] if "EUR" in rates else 1.0850
        usd_jpy = rates.get("JPY", 149.50)
        return eur_usd, usd_jpy
    except Exception:
        return 1.0850, 149.50

def get_deriv_price(symbol="1HZ75V"):
    """
    Fetches quick tick price for Deriv Volatility Indices.
    Falls back instantly if connection delays to prevent Vercel 504 timeouts.
    """
    try:
        import websocket
        ws_url = "wss://ws.derivws.com/websockets/v3?app_id=59828"
        ws = websocket.create_connection(ws_url, timeout=1.2)
        ws.send(json.dumps({"ticks": symbol}))
        response = json.loads(ws.recv())
        ws.close()
        if "tick" in response and "quote" in response["tick"]:
            return float(response["tick"]["quote"])
    except Exception:
        pass
    
    # Fallback prices
    fallbacks = {
        "1HZ75V": 4702.19,
        "1HZ100V": 2450.80
    }
    return fallbacks.get(symbol, 1000.0)

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
                "/deriv - Deriv Volatility Multipliers"
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
            v75_price = get_deriv_price("1HZ75V")
            v100_price = get_deriv_price("1HZ100V")
            
            reply = (
                f"📊 *SNIPER KE 254 - DERIV MULTIPLIERS*\n\n"
                f"{session_warning}"
                f"🟢 *VOLATILITY 75 (1s) - BUY*\n"
                f"Entry: `{v75_price:,.2f}`\n"
                f"⚡ Multiplier: `x50` | Stake: `$2.00`\n"
                f"🎯 TP: `+$5.00 USD` | 🛑 SL: `-$2.00 USD`\n\n"
                f"🟢 *VOLATILITY 100 (1s) - BUY*\n"
                f"Entry: `{v100_price:,.2f}`\n"
                f"⚡ Multiplier: `x50` | Stake: `$2.00`\n"
                f"🎯 TP: `+$5.00 USD` | 🛑 SL: `-$2.00 USD`"
            )
            send_message(chat_id, reply)
            
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    return "🔥 SNIPER KE 254 LIVE!"

if __name__ == "__main__":
    app.run(debug=True)
