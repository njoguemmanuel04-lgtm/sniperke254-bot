import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load the token from Vercel environment variables
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


@app.route("/", methods=["POST"])
def webhook():
  """Endpoint that receives incoming updates from Telegram"""
  data = request.get_json()

  if data and "message" in data:
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").upper()

    # Handle commands
    if "/START" in text or "START" in text:
      reply = (
          "🔥 *SNIPER KE 254 BOT LIVE!* 🔥\n\nCommands:\n/gold - Gold signal\n/"
          "btc - Bitcoin signal\n/forex - Major forex pairs"
      )
      send_message(chat_id, reply)

    elif "/GOLD" in text:
      # Placeholder for live gold data logic
      reply = (
          "🥇 *SNIPER KE 254 - GOLD*\n\nPrice: $2650.20 (Live)\nSignal: BUY"
          " GOLD 📈\n\nTP1: $2658\nSL: $2645\n\n*Risk 1%*"
      )
      send_message(chat_id, reply)

  return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def home():
  """Fallback route so visiting your Vercel URL in a browser shows it's live"""
  return "🔥 SNIPER KE 254 LIVE!"


if __name__ == "__main__":
  app.run(debug=True)
