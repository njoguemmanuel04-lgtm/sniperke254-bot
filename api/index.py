from datetime import datetime, timezone, timedelta
import json
import os
from flask import Flask, jsonify, request
import numpy as np
import pandas as pd
import requests
import yfinance as pandas_yf

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Error sending message: {e}")


def check_market_session():
  eat_tz = timezone(timedelta(hours=3))
  now_eat = datetime.now(eat_tz)
  hour = now_eat.hour

  if 0 <= hour < 9:
    return (
        "⚠️ *SESSION WARNING:* Low-Liquidity Asian Session (00:00 - 09:00 EAT).\n"
        " Trade with caution or wait for London/NY sessions!\n\n"
    )
  return ""


def analyze_smc_signal(ticker_symbol, is_crypto=False, is_gold=False):
  """Pure Smart Money Concepts (SMC) & Liquidity Sweep Engine."""
  try:
    df = pandas_yf.download(ticker_symbol, period="5d", interval="1h", progress=False)
    if df.empty or "Close" not in df or len(df) < 20:
      return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0, "Insufficient Data"

    close_series = df["Close"].iloc[:, 0] if hasattr(df["Close"], "iloc") and len(df["Close"].shape) > 1 else df["Close"]
    high_series = df["High"].iloc[:, 0] if hasattr(df["High"], "iloc") and len(df["High"].shape) > 1 else df["High"]
    low_series = df["Low"].iloc[:, 0] if hasattr(df["Low"], "iloc") and len(df["Low"].shape) > 1 else df["Low"]

    current_price = float(close_series.iloc[-1])
    current_high = float(high_series.iloc[-1])
    current_low = float(low_series.iloc[-1])

    # 1. 8-Hour Liquidity High & Low
    recent_high = float(high_series.iloc[-9:-1].max())
    recent_low = float(low_series.iloc[-9:-1].min())

    # 2. EMA Trend Filter
    ema20 = float(close_series.ewm(span=20, adjust=False).mean().iloc[-1])

    # Dynamic Buffers per Asset Class
    if is_crypto:
      sl_buf, tp1_d, tp2_d = 400.0, 800.0, 1500.0
    elif is_gold:
      sl_buf, tp1_d, tp2_d = 3.0, 12.0, 25.0
    elif "JPY" in ticker_symbol:
      sl_buf, tp1_d, tp2_d = 0.25, 0.50, 0.90
    else:  # Standard Forex Pairs
      sl_buf, tp1_d, tp2_d = 0.0020, 0.0045, 0.0080

    # --- SNIPER SELL LOGIC (Liquidity Sweep High) ---
    if current_high >= recent_high and current_price < ema20:
      sl = max(current_high, recent_high) + sl_buf
      tp1 = current_price - tp1_d
      tp2 = current_price - tp2_d
      return "SELL", current_price, tp1, tp2, sl, "Liquidity Sweep High + Bearish Displacement"

    # --- SNIPER BUY LOGIC (Liquidity Sweep Low) ---
    if current_low <= recent_low and current_price > ema20:
      sl = min(current_low, recent_low) - sl_buf
      tp1 = current_price + tp1_d
      tp2 = current_price + tp2_d
      return "BUY", current_price, tp1, tp2, sl, "Liquidity Sweep Low + Bullish Displacement"

    return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, "Consolidating in Range"

  except Exception as e:
    print(f"SMC Error for {ticker_symbol}: {e}")
    return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0, f"Error: {e}"


@app.route("/", methods=["POST"])
def webhook():
  data = request.get_json()

  if data and "message" in data:
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").upper()
    session_warning = check_market_session()

    if "/START" in text or "START" in text:
      reply = (
          "🎯 *SNIPER KE 254 MANUAL SMC BOT* 🎯\n\n"
          "Commands:\n"
          "/gold - SMC Gold Liquidity Sweep\n"
          "/btc - SMC Bitcoin Liquidity Sweep\n"
          "/allforex - SMC Forex Scan"
      )
      send_message(chat_id, reply)

    elif "/GOLD" in text:
      action, price, tp1, tp2, sl, note = analyze_smc_signal("GC=F", is_gold=True)
      if action == "NO_SIGNAL":
        send_message(chat_id, f"🥇 *SNIPER KE 254 - GOLD*\n\n⏳ *NO SETUP* ({note})\n📍 *Price:* `${price:,.2f}`")
      else:
        emoji = "🟢" if action == "BUY" else "🔴"
        reply = (
            f"🎯 *SNIPER KE 254 - GOLD SMC ENTRY*\n\n{session_warning}"
            f"{emoji} *Signal: {action} GOLD*\n"
            f"📍 *Entry:* `${price:,.2f}`\n💡 *Setup:* `{note}`\n\n"
            f"🎯 *TP1:* `${tp1:,.2f}` | 🎯 *TP2:* `${tp2:,.2f}`\n🛑 *SL:* `${sl:,.2f}`"
        )
        send_message(chat_id, reply)

    elif "/BTC" in text:
      action, price, tp1, tp2, sl, note = analyze_smc_signal("BTC-USD", is_crypto=True)
      if action == "NO_SIGNAL":
        send_message(chat_id, f"₿ *SNIPER KE 254 - BITCOIN*\n\n⏳ *NO SETUP* ({note})\n📍 *Price:* `${price:,.2f}`")
      else:
        emoji = "🟢" if action == "BUY" else "🔴"
        reply = (
            f"🎯 *SNIPER KE 254 - BITCOIN SMC ENTRY*\n\n{session_warning}"
            f"{emoji} *Signal: {action} BITCOIN*\n"
            f"📍 *Entry:* `${price:,.2f}`\n💡 *Setup:* `{note}`\n\n"
            f"🎯 *TP1:* `${tp1:,.2f}` | 🎯 *TP2:* `${tp2:,.2f}`\n🛑 *SL:* `${sl:,.2f}`"
        )
        send_message(chat_id, reply)

    elif "/ALLFOREX" in text or "/FOREXSCAN" in text:
      forex_pairs = [
          ("EUR/USD", "EURUSD=X"), ("GBP/USD", "GBPUSD=X"),
          ("USD/JPY", "USDJPY=X"), ("AUD/USD", "AUDUSD=X"),
          ("USD/CAD", "USDCAD=X"), ("NZD/USD", "NZDUSD=X"),
          ("USD/CHF", "USDCHF=X"),
      ]
      message_blocks = [f"💱 *SNIPER KE 254 - SMC FOREX SCAN*\n\n{session_warning}"]

      for name, symbol in forex_pairs:
        action, price, tp1, tp2, sl, note = analyze_smc_signal(symbol)
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⏳"

        if action in ["BUY", "SELL"]:
          block = f"{emoji} *{name} - {action}*\nEntry: `{price:.5f}` | Setup: `{note}`\nTP: `{tp1:.5f}` | SL: `{sl:.5f}`\n\n"
        else:
          block = f"⏳ *{name} - NO SETUP* | Price: `{price:.5f}`\n\n"
        message_blocks.append(block)

      send_message(chat_id, "".join(message_blocks))

  return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
  return "🔥 SNIPER KE 254 PURE SMC ENGINE ONLINE!"


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
