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
  """Fetch live XAU/USD spot price"""
  try:
    url = "https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT"
    res = requests.get(url, timeout=5).json()
    return float(res["symbols"][0]["price"])
  except Exception:
    return None


def get_live_btc_price():
  """Fetch live Bitcoin spot price"""
  try:
    url = (
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    )
    res = requests.get(url, timeout=5).json()
    return float(res["bitcoin"]["usd"])
  except Exception:
    return None


def get_forex_rates():
  """Fetch live USD exchange rates for EUR and JPY"""
  try:
    url = "https://open.er-api.com/v6/latest/USD"
    res = requests.get(url, timeout=5).json()
    rates = res.get("rates", {})
    eur_usd = 1.0 / rates["EUR"] if "EUR" in rates else None
    usd_jpy = rates.get("JPY")
    return eur_usd, usd_jpy
  except Exception:
    return None, None


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
          " Signal\n/btc - Dynamic Bitcoin Signal\n/forex - Dynamic Forex Signals"
      )
      send_message(chat_id, reply)

    # /gold command - Realistic Spread-Friendly Offsets ($25 SL, $35/$70 TP)
    elif "/GOLD" in text:
      price = get_live_gold_price()
      if price:
        sl = price - 25.0
        tp1 = price + 35.0
        tp2 = price + 70.0

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

    # /btc command - Meaningful Move Offsets ($800 SL, $1200/$2500 TP)
    elif "/BTC" in text:
      price = get_live_btc_price()
      if price:
        sl = price - 800.0
        tp1 = price + 1200.0
        tp2 = price + 2500.0

        reply = (
            f"₿ *SNIPER KE 254 - BITCOIN (BTC/USD)*\n\n"
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

    # /forex command - Live Spot Price Calculation
    elif "/FOREX" in text:
      eur_usd, usd_jpy = get_forex_rates()
      if eur_usd and usd_jpy:
        # EUR/USD Buy setup (30 pips SL, 50 pips TP)
        eur_sl = eur_usd - 0.0030
        eur_tp = eur_usd + 0.0050

        # USD/JPY Sell setup (30 pips SL, 50 pips TP)
        jpy_sl = usd_jpy + 0.30
        jpy_tp = usd_jpy - 0.50

        reply = (
            f"💱 *SNIPER KE 254 - LIVE FOREX SIGNALS*\n\n"
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

  return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
  return "🔥 SNIPER KE 254 LIVE!"


if __name__ == "__main__":
  app.run(debug=True)
