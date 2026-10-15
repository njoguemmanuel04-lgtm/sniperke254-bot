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


def analyze_momentum_signal(ticker_symbol, is_crypto=False, is_gold=False):
    """Triple EMA Engine (20, 50, 200) on M5 with Macro Trend Filtering."""
    try:
        # Fetch enough history to accurately calculate the 200 EMA on M5
        df = pandas_yf.download(ticker_symbol, period="5d", interval="5m", progress=False)
        if df.empty or "Close" not in df or len(df) < 210:
            return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0, "Insufficient Data for 200 EMA"

        close_series = df["Close"].iloc[:, 0] if hasattr(df["Close"], "iloc") and len(df["Close"].shape) > 1 else df["Close"]
        high_series = df["High"].iloc[:, 0] if hasattr(df["High"], "iloc") and len(df["High"].shape) > 1 else df["High"]
        low_series = df["Low"].iloc[:, 0] if hasattr(df["Low"], "iloc") and len(df["Low"].shape) > 1 else df["Low"]

        current_price = float(close_series.iloc[-1])
        current_high = float(high_series.iloc[-1])
        current_low = float(low_series.iloc[-1])

        # 1. Calculate 20, 50, and 200 EMAs
        ema20 = close_series.ewm(span=20, adjust=False).mean()
        ema50 = close_series.ewm(span=50, adjust=False).mean()
        ema200 = close_series.ewm(span=200, adjust=False).mean()

        curr_ema20 = float(ema20.iloc[-1])
        prev_ema20 = float(ema20.iloc[-2])
        curr_ema50 = float(ema50.iloc[-1])
        prev_ema50 = float(ema50.iloc[-2])
        curr_ema200 = float(ema200.iloc[-1])

        # Dynamic Buffers per Asset Class
        if is_crypto:
            sl_buf, tp1_d, tp2_d = 150.0, 300.0, 600.0
        elif is_gold:
            sl_buf, tp1_d, tp2_d = 1.5, 4.0, 8.0
        elif "JPY" in ticker_symbol:
            sl_buf, tp1_d, tp2_d = 0.10, 0.25, 0.50
        else:
            sl_buf, tp1_d, tp2_d = 0.0008, 0.0018, 0.0035

        # --- BULLISH TRIPLE EMA SETUP (BUY) ---
        # Rules: 20 > 50 EMA, and price/EMAs must be strictly above the 200 EMA macro filter
        if (curr_ema20 > curr_ema50) and (curr_ema20 > curr_ema200) and (current_price > curr_ema20):
            # Check if a fresh crossover happened or strong continuation
            if (prev_ema20 <= prev_ema50) or (current_price > curr_ema20):
                sl = current_low - sl_buf
                tp1 = current_price + tp1_d
                tp2 = current_price + tp2_d
                return "BUY", current_price, tp1, tp2, sl, "Triple EMA Bullish Trend (Above 200 EMA)"

        # --- BEARISH TRIPLE EMA SETUP (SELL) ---
        # Rules: 20 < 50 EMA, and price/EMAs must be strictly below the 200 EMA macro filter
        if (curr_ema20 < curr_ema50) and (curr_ema20 < curr_ema200) and (current_price < curr_ema20):
            if (prev_ema20 >= prev_ema50) or (current_price < curr_ema20):
                sl = current_high + sl_buf
                tp1 = current_price - tp1_d
                tp2 = current_price - tp2_d
                return "SELL", current_price, tp1, tp2, sl, "Triple EMA Bearish Trend (Below 200 EMA)"

        return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0, "Consolidating / Against 200 EMA Bias"

    except Exception as e:
        print(f"Triple EMA Engine Error for {ticker_symbol}: {e}")
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
                "🎯 *SNIPER KE 254 (TRIPLE EMA 20/50/200)* 🎯\n\n"
                "Commands:\n"
                "/gold - M5 Gold Macro Trend\n"
                "/btc - M5 Bitcoin Macro Trend\n"
                "/allforex - M5 Forex Macro Scan"
            )
            send_message(chat_id, reply)

        elif "/GOLD" in text:
            action, price, tp1, tp2, sl, note = analyze_momentum_signal("GC=F", is_gold=True)
            if action == "NO_SIGNAL":
                send_message(chat_id, f"🥇 *SNIPER KE 254 - GOLD (M5)*\n\n⏳ *NO SETUP* ({note})\n📍 *Price:* `${price:,.2f}`")
            else:
                emoji = "🟢" if action == "BUY" else "🔴"
                reply = (
                    f"🎯 *SNIPER KE 254 - GOLD M5 ENTRY*\n\n{session_warning}"
                    f"{emoji} *Signal: {action} GOLD*\n"
                    f"📍 *Entry:* `${price:,.2f}`\n💡 *Setup:* `{note}`\n\n"
                    f"🎯 *TP1:* `${tp1:,.2f}` | 🎯 *TP2:* `${tp2:,.2f}`\n🛑 *SL:* `${sl:,.2f}`"
                )
                send_message(chat_id, reply)

        elif "/BTC" in text:
            action, price, tp1, tp2, sl, note = analyze_momentum_signal("BTC-USD", is_crypto=True)
            if action == "NO_SIGNAL":
                send_message(chat_id, f"₿ *SNIPER KE 254 - BITCOIN (M5)*\n\n⏳ *NO SETUP* ({note})\n📍 *Price:* `${price:,.2f}`")
            else:
                emoji = "🟢" if action == "BUY" else "🔴"
                reply = (
                    f"🎯 *SNIPER KE 254 - BITCOIN M5 ENTRY*\n\n{session_warning}"
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
            message_blocks = [f"💱 *SNIPER KE 254 - TRIPLE EMA SCAN*\n\n{session_warning}"]

            for name, symbol in forex_pairs:
                action, price, tp1, tp2, sl, note = analyze_momentum_signal(symbol)
                emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⏳"

                if action in ["BUY", "SELL"]:
                    block = f"{emoji} *{name} - {action} (M5)*\nEntry: `{price:.5f}` | Setup: `{note}`\nTP: `{tp1:.5f}` | SL: `{sl:.5f}`\n\n"
                else:
                    block = f"⏳ *{name} - NO SETUP* | Price: `{price:.5f}`\n\n"
                message_blocks.append(block)

            send_message(chat_id, "".join(message_blocks))

    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
    return "🔥 SNIPER KE 254 TRIPLE EMA ENGINE ONLINE!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
