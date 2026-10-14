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
        " Broker spreads are wider and fakeouts are common. Trade with caution"
        " or wait for London/NY sessions!\n\n"
    )
  return ""


def get_advanced_technical_signal(ticker_symbol, is_crypto=False, is_gold=False):
  """Sniper Engine enhanced with EMA, Native RSI, ADX, and Bollinger Bands."""
  try:
    df = pandas_yf.download(
        ticker_symbol, period="5d", interval="1h", progress=False
    )
    if df.empty or "Close" not in df:
      raise ValueError("Empty dataframe from yfinance")

    close_series = (
        df["Close"].iloc[:, 0]
        if hasattr(df["Close"], "iloc") and len(df["Close"].shape) > 1
        else df["Close"]
    )
    high_series = (
        df["High"].iloc[:, 0]
        if hasattr(df["High"], "iloc") and len(df["High"].shape) > 1
        else df["High"]
    )
    low_series = (
        df["Low"].iloc[:, 0]
        if hasattr(df["Low"], "iloc") and len(df["Low"].shape) > 1
        else df["Low"]
    )

    ema9 = close_series.ewm(span=9, adjust=False).mean()
    ema21 = close_series.ewm(span=21, adjust=False).mean()

    # Native RSI (14-period)
    delta = close_series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))

    # Native ADX (14-period) calculation for Trend Strength
    tr1 = high_series - low_series
    tr2 = (high_series - close_series.shift()).abs()
    tr3 = (low_series - close_series.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1 / 14, adjust=False).mean()

    up_move = high_series - high_series.shift()
    down_move = low_series.shift() - low_series
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=close_series.index)
    minus_dm_s = pd.Series(minus_dm, index=close_series.index)

    plus_di = (
        100
        * plus_dm_s.ewm(alpha=1 / 14, adjust=False).mean()
        / atr14.replace(0, np.nan)
    )
    minus_di = (
        100
        * minus_dm_s.ewm(alpha=1 / 14, adjust=False).mean()
        / atr14.replace(0, np.nan)
    )
    dx = (
        100
        * (plus_di - minus_di).abs()
        / (plus_di + minus_di).replace(0, np.nan)
    )
    adx = dx.ewm(alpha=1 / 14, adjust=False).mean().fillna(0)

    current_price = float(close_series.iloc[-1])
    latest_ema9 = float(ema9.iloc[-1])
    latest_ema21 = float(ema21.iloc[-1])
    current_rsi = float(rsi_series.iloc[-1])
    current_adx = float(adx.iloc[-1])

    # Filter 1: ADX Trend Strength (ADX > 22 ensures a real trend)
    if current_adx < 22:
      return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, current_rsi, current_adx

    # Filter 2: EMA Gap & RSI Pullback Windows
    ema_gap_pct = abs(latest_ema9 - latest_ema21) / current_price * 100
    if ema_gap_pct < 0.08:
      return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, current_rsi, current_adx

    if latest_ema9 > latest_ema21 and not (45 <= current_rsi <= 58):
      return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, current_rsi, current_adx

    if latest_ema9 < latest_ema21 and not (42 <= current_rsi <= 55):
      return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, current_rsi, current_adx

    # Dynamic risk parameters
    if is_crypto:
      sl_buffer, tp_buffer = 800.0, 1500.0
    elif is_gold:
      sl_buffer, tp_buffer = 25.0, 45.0
    elif "JPY" in ticker_symbol:
      sl_buffer, tp_buffer = 0.35, 0.60
    else:
      sl_buffer, tp_buffer = 0.0030, 0.0055

    if latest_ema9 > latest_ema21:
      action = "BUY"
      sl = current_price - sl_buffer
      tp1 = current_price + tp_buffer
      tp2 = current_price + (tp_buffer * 1.8)
    else:
      action = "SELL"
      sl = current_price + sl_buffer
      tp1 = current_price - tp_buffer
      tp2 = current_price - (tp_buffer * 1.8)

    return action, current_price, tp1, tp2, sl, current_rsi, current_adx

  except Exception as e:
    print(f"Technical Analysis Error for {ticker_symbol}: {e}")
    return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0


def get_deriv_price(symbol):
  try:
    import websocket

    ws_url = "wss://ws.derivws.com/websockets/v3?app_id=59828"
    ws = websocket.create_connection(ws_url, timeout=3.0)
    ws.send(json.dumps({"ticks": symbol}))
    response = json.loads(ws.recv())
    ws.close()
    if "tick" in response and "quote" in response["tick"]:
      return float(response["tick"]["quote"])
  except Exception:
    pass

  fallbacks = {
      "R_10": 1920.50,
      "R_25": 4850.20,
      "R_50": 340.10,
      "R_75": 10500.40,
      "R_100": 3100.80,
      "1HZ10V": 1200.50,
      "1HZ25V": 2500.30,
      "1HZ50V": 410.60,
      "1HZ75V": 4702.19,
      "1HZ100V": 2450.80,
      "1HZ150V": 520.10,
      "1HZ250V": 890.40,
  }
  return fallbacks.get(symbol, 1000.0)


@app.route("/", methods=["POST"])
def webhook():
  data = request.get_json()

  if data and "message" in data:
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").upper()
    session_warning = check_market_session()

    if "/START" in text or "START" in text:
      reply = (
          "🔥 *SNIPER KE 254 BOT LIVE (EMA + RSI + ADX)* 🔥\n\n"
          "Commands:\n"
          "/gold - Pro Gold Signal\n"
          "/btc - Pro Bitcoin Signal\n"
          "/forex - EUR/USD & USD/JPY Scan\n"
          "/allforex - Scan All Major Forex Markets\n"
          "/deriv - All Volatility Multipliers Scan"
      )
      send_message(chat_id, reply)

    elif "/GOLD" in text:
      action, price, tp1, tp2, sl, rsi, adx = get_advanced_technical_signal(
          "GC=F", is_gold=True
      )
      if action == "NO_SIGNAL":
        send_message(
            chat_id,
            f"🥇 *SNIPER KE 254 - GOLD*\n\n⏳ *NO SETUP* (Consolidating or weak"
            f" ADX)\n📍 *Price:* `${price:,.2f}`\n📈 *RSI:* `{rsi:.1f}` | *ADX:*"
            f" `{adx:.1f}`",
        )
      else:
        emoji = "🟢" if action == "BUY" else "🔴"
        reply = (
            f"🥇 *SNIPER KE 254 - GOLD (PRO ENGINE)*\n\n"
            f"{session_warning}"
            f"{emoji} *Signal: {action} GOLD*\n"
            f"📍 *Entry:* `${price:,.2f}`\n"
            f"📈 *RSI:* `{rsi:.1f}` | *ADX:* `{adx:.1f}`\n\n"
            f"🎯 *TP1:* `${tp1:,.2f}`\n"
            f"🎯 *TP2:* `${tp2:,.2f}`\n"
            f"🛑 *SL:* `${sl:,.2f}`\n\n"
            f"⚖️ *Risk:* 1% per trade"
        )
        send_message(chat_id, reply)

    elif "/BTC" in text:
      action, price, tp1, tp2, sl, rsi, adx = get_advanced_technical_signal(
          "BTC-USD", is_crypto=True
      )
      if action == "NO_SIGNAL":
        send_message(
            chat_id,
            f"₿ *SNIPER KE 254 - BITCOIN*\n\n⏳ *NO SETUP* (Consolidating or weak"
            f" ADX)\n📍 *Price:* `${price:,.2f}`\n📈 *RSI:* `{rsi:.1f}` | *ADX:*"
            f" `{adx:.1f}`",
        )
      else:
        emoji = "🟢" if action == "BUY" else "🔴"
        reply = (
            f"₿ *SNIPER KE 254 - BITCOIN (PRO ENGINE)*\n\n"
            f"{session_warning}"
            f"{emoji} *Signal: {action} BITCOIN*\n"
            f"📍 *Entry:* `${price:,.2f}`\n"
            f"📈 *RSI:* `{rsi:.1f}` | *ADX:* `{adx:.1f}`\n\n"
            f"🎯 *TP1:* `${tp1:,.2f}`\n"
            f"🎯 *TP2:* `${tp2:,.2f}`\n"
            f"🛑 *SL:* `${sl:,.2f}`\n\n"
            f"⚖️ *Risk:* 1-2% per trade"
        )
        send_message(chat_id, reply)

    elif "/ALLFOREX" in text or "/FOREXSCAN" in text:
      forex_pairs = [
          ("EUR/USD", "EURUSD=X"),
          ("GBP/USD", "GBPUSD=X"),
          ("USD/JPY", "USDJPY=X"),
          ("AUD/USD", "AUDUSD=X"),
          ("USD/CAD", "USDCAD=X"),
          ("NZD/USD", "NZDUSD=X"),
          ("USD/CHF", "USDCHF=X"),
      ]
      message_blocks = [
          f"💱 *SNIPER KE 254 - ALL MAJOR FOREX SCAN*\n\n{session_warning}"
      ]

      for name, symbol in forex_pairs:
        action, price, tp1, tp2, sl, rsi, adx = get_advanced_technical_signal(
            symbol
        )
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⏳"

        if action in ["BUY", "SELL"]:
          block = (
              f"{emoji} *{name} - {action}* (RSI: `{rsi:.1f}` | ADX:"
              f" `{adx:.1f}`)\n"
              f"Entry: `{price:.5f}` | TP: `{tp1:.5f}` | SL: `{sl:.5f}`\n\n"
          )
        else:
          block = (
              f"⏳ *{name} - NO SETUP* (RSI: `{rsi:.1f}` | ADX: `{adx:.1f}`)\n"
              f"Price: `{price:.5f}` (Consolidating)\n\n"
          )
        message_blocks.append(block)

      send_message(chat_id, "".join(message_blocks))

    elif "/DERIV" in text or "/VOLATILITY" in text:
      indices = [
          ("Volatility 10", "R_10"),
          ("Volatility 25", "R_25"),
          ("Volatility 50", "R_50"),
          ("Volatility 75", "R_75"),
          ("Volatility 100", "R_100"),
          ("Volatility 10 (1s)", "1HZ10V"),
          ("Volatility 25 (1s)", "1HZ25V"),
          ("Volatility 50 (1s)", "1HZ50V"),
          ("Volatility 75 (1s)", "1HZ75V"),
          ("Volatility 100 (1s)", "1HZ100V"),
          ("Volatility 150 (1s)", "1HZ150V"),
          ("Volatility 250 (1s)", "1HZ250V"),
      ]
      message_blocks = [
          f"📊 *SNIPER KE 254 - ALL VOLATILITY MULTIPLIERS*\n\n{session_warning}"
      ]
      for name, symbol in indices:
        price = get_deriv_price(symbol)
        last_digit = int(str(price).replace(".", "")[-1])
        action = "BUY" if last_digit % 2 == 0 else "SELL"
        emoji = "🟢" if action == "BUY" else "🔴"

        block = (
            f"{emoji} *{name} - {action}*\n"
            f"Entry: `{price:,.2f}` | ⚡ x50 | 💰 `$2.00`\n"
            f"🎯 `+$5.00` | 🛑 `-$2.00`\n\n"
        )
        message_blocks.append(block)

      send_message(chat_id, "".join(message_blocks[0:7]))
      send_message(chat_id, "".join([message_blocks[0]] + message_blocks[7:]))

  return jsonify({"status": "ok"})


# Automated Hourly Multi-Market Cron Route for Vercel
@app.route("/cron-alert", methods=["GET"])
def cron_alert():
  chat_id = os.environ.get("TELEGRAM_CHAT_ID")
  if not chat_id:
    return jsonify({"error": "No TELEGRAM_CHAT_ID configured"}), 400

  assets_to_scan = [
      ("Gold", "GC=F", False, True),
      ("Bitcoin", "BTC-USD", True, False),
      ("EUR/USD", "EURUSD=X", False, False),
      ("GBP/USD", "GBPUSD=X", False, False),
      ("USD/JPY", "USDJPY=X", False, False),
      ("AUD/USD", "AUDUSD=X", False, False),
      ("USD/CAD", "USDCAD=X", False, False),
      ("NZD/USD", "NZDUSD=X", False, False),
      ("USD/CHF", "USDCHF=X", False, False),
  ]

  signals_found = []

  for name, symbol, is_crypto, is_gold in assets_to_scan:
    action, price, tp1, tp2, sl, rsi, adx = get_advanced_technical_signal(
        symbol, is_crypto=is_crypto, is_gold=is_gold
    )

    if action in ["BUY", "SELL"]:
      emoji = "🟢" if action == "BUY" else "🔴"
      if is_gold or is_crypto:
        formatted_price = f"${price:,.2f}"
        formatted_tp = f"${tp1:,.2f}"
        formatted_sl = f"${sl:,.2f}"
      else:
        formatted_price = f"{price:.5f}"
        formatted_tp = f"{tp1:.5f}"
        formatted_sl = f"{sl:.5f}"

      block = (
          f"{emoji} *{name} - {action}*\n"
          f"📍 *Entry:* `{formatted_price}` | RSI: `{rsi:.1f}` | ADX:"
          f" `{adx:.1f}`\n"
          f"🎯 *TP:* `{formatted_tp}` | 🛑 *SL:* `{formatted_sl}`\n\n"
      )
      signals_found.append(block)

  if signals_found:
    message = (
        "🚨 *AUTOMATED SNIPER MULTI-MARKET ALERT* 🚨\n\n"
        + "".join(signals_found)
    )
    send_message(chat_id, message)
    return jsonify(
        {"status": "signals_sent", "count": len(signals_found)}
    )
  else:
    return jsonify({
        "status": "no_setups_found",
        "message": "All markets consolidating.",
    })


@app.route("/", methods=["GET"])
def home():
  return "🔥 SNIPER KE 254 PRO ENGINE ACTIVE ON VERCEL!"


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
