
import os
import re
import json
import logging
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from telegram.ext import Updater, MessageHandler, Filters

load_dotenv("config.env")

# Binance
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

# Config
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
usd_amount = float(os.getenv("POSITION_USDT", 100))

# Regex para formato visual
regex = re.compile(r"\*([A-Z]+(?:USDT|USDC))\*.*?Tipo:\s*(BUY|SELL).*?Precio:\s*(\d+\.?\d*|mercado).*?TP.*?:\s*(\d+\.?\d*).*?SL.*?:\s*(\d+\.?\d*)", re.DOTALL)

def ejecutar_trade(symbol, side, entry_price, tp, sl, capital=None):
    try:
        if entry_price.lower() == "mercado":
            mark_price_data = client.futures_mark_price(symbol=symbol)
            mark_price = float(mark_price_data['markPrice'])
        else:
            mark_price = float(entry_price)

        capital = capital if capital is not None else usd_amount
        quantity = round(capital / mark_price, 3)

        print(f"🚀 Ejecutando orden MARKET: {side} {symbol} con {quantity} contratos")

        order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY if side.upper() == "BUY" else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity,
            positionSide="LONG" if side.upper() == "BUY" else "SHORT"
        )

        print(f"✅ Orden ejecutada en Binance: {order}")
    except Exception as e:
        print(f"❌ Error al ejecutar orden en Binance: {e}")

def procesar_mensaje(update, context):
    try:
        text = update.message.text
        print("📩 Mensaje recibido:")
        print(text)

        # Primero intenta como JSON puro
        try:
            data = json.loads(text)
            if all(k in data for k in ["symbol", "side", "tp", "sl", "capital"]):
                ejecutar_trade(
                    symbol=data["symbol"],
                    side=data["side"],
                    entry_price="mercado",
                    tp=data["tp"],
                    sl=data["sl"],
                    capital=float(data["capital"])
                )
                return
        except json.JSONDecodeError:
            pass  # No era JSON, seguimos con regex

        # Luego intenta como mensaje visual
        match = regex.search(text)
        if match:
            symbol, side, entry, tp, sl = match.groups()
            ejecutar_trade(symbol, side, entry, tp, sl)
        else:
            print("⚠️ Formato no reconocido (ni JSON ni visual)")

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

def procesar_senal_desde_archivo():
    try:
        with open("señal.txt", "r") as f:
            text = f.read().strip()
        print(f"📝 Señal desde archivo:\n{text}")
        match = regex.search(text)
        if match:
            symbol, side, entry, tp, sl = match.groups()
            ejecutar_trade(symbol, side, entry, tp, sl)
        else:
            print("⚠️ Formato de señal no válido en archivo")
    except Exception as e:
        print(f"❌ Error al procesar archivo: {e}")

if __name__ == '__main__':
    procesar_senal_desde_archivo()
    logging.basicConfig(level=logging.INFO)
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_mensaje))
    print("🤖 Bot híbrido escuchando mensajes de Telegram...")
    updater.start_polling()
    updater.idle()
