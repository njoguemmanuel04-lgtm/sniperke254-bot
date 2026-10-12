import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load bot token from environment variables
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
    price = float(res["symbols"][0]["price"])
    return f"${price:,.2f}"
  except Exception:
    return "Market Data Unavailable"


def get_live_btc_price():
  """Fetch live Bitcoin price"""
  try:
    url = (
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    )
    res = requests.get(url, timeout=5).json()
    price = res["bitcoin"]["usd"]
    return f"${price:,.2f}"
  except Exception:
    return "Market Data Unavailable"


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
          "🔥 *SNIPER KE 254 BOT LIVE!* 🔥\n\nCommands:\n/gold - Live Gold"
          " Signal\n/btc - Live Bitcoin Signal\n/forex - Major Forex Pairs"
      )
      send_message(chat_id, reply)

    # /gold command
    elif "/GOLD" in text:
      live_price = get_live_gold_price()
      reply = (
          f"🥇 *SNIPER KE 254 - GOLD (XAU/USD)*\n\nLive Price:"
          f" {live_price}\nSignal: *BUY GOLD* 📈\n\n*Risk: 1%*"
      )
      send_message(chat_id, reply)

    # /btc command
    elif "/BTC" in text:
      live_price = get_live_btc_price()
      reply = (
          f"₿ *SNIPER KE 254 - BITCOIN (BTC/USD)*\n\nLive Price:"
          f" {live_price}\nSignal: *BULLISH ACCUMULATION* 🚀\n\n*Risk: 2%*"
      )
      send_message(chat_id, reply)

    # /forex command
    elif "/FOREX" in text:
      reply = (
          "💱 *SNIPER KE 254 - FOREX WATCHLIST*\n\n• EUR/USD: Bullish"
          " Reversal\n• GBP/USD: Ranging\n• USD/JPY: Bearish Momentum"
      )
      send_message(chat_id, reply)

  return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
  return "🔥 SNIPER KE 254 LIVE!"


if __name__ == "__main__":
  app.run(debug=True)
