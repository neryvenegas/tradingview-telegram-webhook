from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route("/", methods=["GET"])
def home():
    return "Webhook activo - esperando POST de TradingView."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    mensaje = "📢 *Alerta de TradingView*\n\n"
    for key, value in data.items():
        mensaje += f"🔹 *{key}*: `{value}`\n"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)