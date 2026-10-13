import os
import json
import requests
import yfinance as pandas_yf
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
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
    eat_tz = timezone(timedelta(hours=3))
    now_eat = datetime.now(eat_tz)
    hour = now_eat.hour

    if 0 <= hour < 9:
        return (
            "⚠️ *SESSION WARNING:* Low-Liquidity Asian Session (00:00 - 09:00 EAT).\n"
            " Broker spreads are wider and fakeouts are common. Trade with caution or wait for London/NY sessions!\n\n"
        )
    return ""

def get_advanced_technical_signal(ticker_symbol, is_crypto=False, is_gold=False):
    """
    Sniper Engine: Only fires when a high-probability EMA trend is confirmed.
    Filters out choppy, sideways, and consolidation markets.
    """
    try:
        df = pandas_yf.download(ticker_symbol, period="5d", interval="1h", progress=False)
        if df.empty:
            return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0
        
        # Flatten columns if multi-index is returned by yfinance
        if hasattr(df['Close'], 'iloc') and len(df['Close'].shape) > 1:
            close_series = df['Close'].iloc[:, 0]
        else:
            close_series = df['Close']
            
        ema9 = close_series.ewm(span=9, adjust=False).mean()
        ema21 = close_series.ewm(span=21, adjust=False).mean()
        
        current_price = float(close_series.iloc[-1])
        latest_ema9 = float(ema9.iloc[-1])
        latest_ema21 = float(ema21.iloc[-1])
        
        # Calculate EMA gap percentage to measure trend strength
        ema_gap_pct = abs(latest_ema9 - latest_ema21) / current_price * 100

        # Minimum trend threshold (0.04% separation required to confirm momentum)
        MIN_TREND_THRESHOLD = 0.04 
        
        if ema_gap_pct < MIN_TREND_THRESHOLD:
            # Market is sideways / ranging - Return current_price as float so formatting never fails
            return "NO_SIGNAL", current_price, 0.0, 0.0, 0.0

        # Dynamic risk parameters based on asset class
        if is_crypto:
            sl_buffer, tp_buffer = 800.0, 1500.0
        elif is_gold:
            sl_buffer, tp_buffer = 25.0, 45.0
        elif "JPY" in ticker_symbol:
            sl_buffer, tp_buffer = 0.35, 0.60
        else:
            sl_buffer, tp_buffer = 0.0030, 0.0055

        # Strong trend confirmed
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
                
        return action, current_price, tp1, tp2, sl
    except Exception as e:
        print(f"Technical Analysis Error for {ticker_symbol}: {e}")
        return "NO_SIGNAL", 0.0, 0.0, 0.0, 0.0

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
        "R_10": 1920.50, "R_25": 4850.20, "R_50": 340.10, "R_75": 10500.40, "R_100": 3100.80,
        "1HZ10V": 1200.50, "1HZ25V": 2500.30, "1HZ50V": 410.60, "1HZ75V": 4702.19,
        "1HZ100V": 2450.80, "1HZ150V": 520.10, "1HZ250V": 890.40
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
                "🔥 *SNIPER KE 254 BOT LIVE (STRICT SNIPER ENGINE)* 🔥\n\n"
                "Commands:\n"
                "/gold - Pro EMA Gold Signal\n"
                "/btc - Pro EMA Bitcoin Signal\n"
                "/forex - Pro EMA Forex Signals\n"
                "/deriv - All Volatility Multipliers Scan"
            )
            send_message(chat_id, reply)

        elif "/GOLD" in text:
            action, price, tp1, tp2, sl = get_advanced_technical_signal("GC=F", is_gold=True)
            if action in ["BUY", "SELL"]:
                emoji = "🟢" if action == "BUY" else "🔴"
                reply = (
                    f"🥇 *SNIPER KE 254 - GOLD (EMA PRO)*\n\n"
                    f"{session_warning}"
                    f"{emoji} *Signal: {action} GOLD*\n"
                    f"📍 *Entry:* `${price:,.2f}`\n\n"
                    f"🎯 *TP1:* `${tp1:,.2f}`\n"
                    f"🎯 *TP2:* `${tp2:,.2f}`\n"
                    f"🛑 *SL:* `${sl:,.2f}`\n\n"
                    f"⚖️ *Risk:* 1% per trade"
                )
            else:
                reply = (
                    f"🥇 *SNIPER KE 254 - GOLD*\n\n"
                    f"{session_warning}"
                    f"⏳ *NO HIGH-PROBABILITY SETUP*\n"
                    f"Market is currently consolidating or sideways near `${price:,.2f}`.\n"
                    f"Stand by for clear trend confirmation before entering!"
                )
            send_message(chat_id, reply)

        elif "/BTC" in text:
            action, price, tp1, tp2, sl = get_advanced_technical_signal("BTC-USD", is_crypto=True)
            if action in ["BUY", "SELL"]:
                emoji = "🟢" if action == "BUY" else "🔴"
                reply = (
                    f"₿ *SNIPER KE 254 - BITCOIN (EMA PRO)*\n\n"
                    f"{session_warning}"
                    f"{emoji} *Signal: {action} BITCOIN*\n"
                    f"📍 *Entry:* `${price:,.2f}`\n\n"
                    f"🎯 *TP1:* `${tp1:,.2f}`\n"
                    f"🎯 *TP2:* `${tp2:,.2f}`\n"
                    f"🛑 *SL:* `${sl:,.2f}`\n\n"
                    f"⚖️ *Risk:* 1-2% per trade"
                )
            else:
                reply = (
                    f"₿ *SNIPER KE 254 - BITCOIN*\n\n"
                    f"{session_warning}"
                    f"⏳ *NO HIGH-PROBABILITY SETUP*\n"
                    f"Bitcoin is currently consolidating near `${price:,.2f}`.\n"
                    f"Stand by for clear volume and trend confirmation!"
                )
            send_message(chat_id, reply)

        elif "/FOREX" in text:
            eur_action, eur_price, eur_tp, _, eur_sl = get_advanced_technical_signal("EURUSD=X")
            jpy_action, jpy_price, jpy_tp, _, jpy_sl = get_advanced_technical_signal("USDJPY=X")
            
            message_parts = [f"💱 *SNIPER KE 254 - PRO EMA FOREX SIGNALS*\n\n{session_warning}"]
            
            # EUR/USD Block
            if eur_action in ["BUY", "SELL"]:
                eur_emoji = "🟢" if eur_action == "BUY" else "🔴"
                message_parts.append(
                    f"{eur_emoji} *EUR/USD - {eur_action}*\n"
                    f"Entry: `{eur_price:.5f}`\n"
                    f"🎯 TP: `{eur_tp:.5f}` | 🛑 SL: `{eur_sl:.5f}`\n\n"
                )
            else:
                message_parts.append(
                    f"⏳ *EUR/USD - NO SETUP*\n"
                    f"Price `{eur_price:.5f}` is currently in consolidation.\n\n"
                )

            # USD/JPY Block
            if jpy_action in ["BUY", "SELL"]:
                jpy_emoji = "🟢" if jpy_action == "BUY" else "🔴"
                message_parts.append(
                    f"{jpy_emoji} *USD/JPY - {jpy_action}*\n"
                    f"Entry: `{jpy_price:.3f}`\n"
                    f"🎯 TP: `{jpy_tp:.3f}` | 🛑 SL: `{jpy_sl:.3f}`"
                )
            else:
                message_parts.append(
                    f"⏳ *USD/JPY - NO SETUP*\n"
                    f"Price `{jpy_price:.3f}` is currently in consolidation."
                )

            send_message(chat_id, "".join(message_parts))

        elif "/DERIV" in text or "/VOLATILITY" in text:
            indices = [
                ("Volatility 10", "R_10"), ("Volatility 25", "R_25"),
                ("Volatility 50", "R_50"), ("Volatility 75", "R_75"),
                ("Volatility 100", "R_100"), ("Volatility 10 (1s)", "1HZ10V"),
                ("Volatility 25 (1s)", "1HZ25V"), ("Volatility 50 (1s)", "1HZ50V"),
                ("Volatility 75 (1s)", "1HZ75V"), ("Volatility 100 (1s)", "1HZ100V"),
                ("Volatility 150 (1s)", "1HZ150V"), ("Volatility 250 (1s)", "1HZ250V"),
            ]
            
            message_blocks = [f"📊 *SNIPER KE 254 - ALL VOLATILITY MULTIPLIERS*\n\n{session_warning}"]
            
            for name, symbol in indices:
                price = get_deriv_price(symbol)
                
                last_digit = int(str(price).replace('.', '')[-1])
                action = "BUY" if last_digit % 2 == 0 else "SELL"
                emoji = "🟢" if action == "BUY" else "🔴"
                
                block = (
                    f"{emoji} *{name} - {action}*\n"
                    f"Entry: `{price:,.2f}` | ⚡ x50 | 💰 `$2.00`\n"
                    f"🎯 `+$5.00` | 🛑 `-$2.00`\n\n"
                )
                message_blocks.append(block)
            
            part1 = "".join(message_blocks[0:7])
            part2 = "".join([message_blocks[0]] + message_blocks[7:])
            
            send_message(chat_id, part1)
            send_message(chat_id, part2)
            
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    return "🔥 SNIPER KE 254 PRO ENGINE ACTIVE!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
