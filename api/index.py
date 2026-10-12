import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load token from environment variables
TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
  """Helper function to send messages back to Telegram"""
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": text,
      "parse_mode": "Markdown",
  }
  requests.post(url, json=payload)


def get_live_gold_price():
  """Fetch live XAU/USD price"""
  try:
    url = "https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT"
    res = requests.get(url, timeout=5).json()
    return float(res["symbols"][0]["price"])
  except Exception:
    return None


def get_live_btc_price():
  """Fetch live Bitcoin price"""
  try:
    url = (
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    )
    res = requests.get(url, timeout=5).json()
    return float(res["bitcoin"]["usd"])
  except Exception:
    return None


@app.route("/", methods=["POST"])
def webhook():
  """Endpoint that receives incoming updates from Telegram"""
  data = request.get_json()

  if data and "message" in data:
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").upper()

    # /start or general menu
    if "/START" in text or "START" in text:
      reply = (
          "🔥 *SNIPER KE 254 BOT LIVE!* 🔥\n\nCommands:\n/gold - Dynamic Gold"
          " Signal\n/btc - Dynamic Bitcoin Signal\n/forex - Forex Signals"
      )
      send_message(chat_id, reply)

    # /gold command with dynamic TP & SL
    elif "/GOLD" in text:
      price = get_live_gold_price()
      if price:
        # Calculate levels based on a $10 Stop Loss and $15/$30 Take Profits
        sl = price - 10.0
        tp1 = price + 15.0
        tp2 = price + 30.0

        reply = (
            f"🥇 *SNIPER KE 254 - GOLD (XAU/USD)*\n\n"
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

    # /btc command with dynamic TP & SL
    elif "/BTC" in text:
      price = get_live_btc_price()
      if price:
        # Calculate levels based on a $1,000 Stop Loss and $1,500/$3,000 Take Profits
        sl = price - 1000.0
        tp1 = price + 1500.0
        tp2 = price + 3000.0

        reply = (
            f"₿ *SNIPER KE 254 - BITCOIN (BTC/USD)*\n\n"
            f"📍 *Entry (Live):* ${price:,.2f}\n"
            f"🚀 *Signal:* BUY BITCOIN\n\n"
            f"🎯 *TP1:* ${tp1:,.2f}\n"
            f"🎯 *TP2:* ${tp2:,.2f}\n"
            f"🛑 *SL:* ${sl:,.2f}\n\n"
            f"⚖️ *Risk:* 2% per trade"
        )
      else:
        reply = "⚠️ *Error:* Live Bitcoin data currently unavailable."
      send_message(chat_id, reply)

    # /forex command
    elif "/FOREX" in text:
      reply = (
          "💱 *SNIPER KE 254 - FOREX SIGNALS*\n\n"
          "🟢 *EUR/USD - BUY*\nEntry: 1.0850\nTP: 1.0920 | SL: 1.0810\n\n"
          "🔴 *USD/JPY - SELL*\nEntry: 149.20\nTP: 148.10 | SL: 149.80"
      )
      send_message(chat_id, reply)

  return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
  return "🔥 SNIPER KE 254 LIVE!"


if __name__ == "__main__":
  app.run(debug=True)
