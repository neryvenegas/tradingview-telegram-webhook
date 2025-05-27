import os
from flask import Flask, request
import telegram

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    mensaje = data.get("text", "Sin contenido")
    bot.send_message(chat_id=CHAT_ID, text=f"📩 Mensaje recibido:\n{mensaje}")
    return "OK", 200
