import os
import json
import math
import requests
from flask import Flask, request
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
usd_amount = float(os.getenv("POSITION_USDT", 100))

app = Flask(__name__)

def enviar_mensaje_telegram(texto):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

def get_precision(symbol):
    info = client.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    return abs(int(round(-1 * math.log10(step_size))))
    raise Exception("No se pudo obtener la precisión del símbolo")

def colocar_tp_sl(symbol, side, qty, tp, sl):
    try:
        side = side.upper()
        positionSide = "LONG" if side == "BUY" else "SHORT"
        opposite_side = "SELL" if side == "BUY" else "BUY"

        client.futures_create_order(
            symbol=symbol,
            side=opposite_side,
            type="STOP_MARKET",
            quantity=qty,
            stopPrice=sl,
            positionSide=positionSide,
            workingType="MARK_PRICE",
            timeInForce="GTC"
        )

        client.futures_create_order(
            symbol=symbol,
            side=opposite_side,
            type="TAKE_PROFIT_MARKET",
            quantity=qty,
            stopPrice=tp,
            positionSide=positionSide,
            workingType="MARK_PRICE",
            timeInForce="GTC"
        )
    except Exception as e:
        print(f"⚠️ Error al colocar TP/SL: {e}")
        enviar_mensaje_telegram(f"⚠️ Error colocando TP/SL: {e}")

def ejecutar_trade(symbol, side, tp, sl, capital=None):
    try:
        mark_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])

        if capital is None:
            symbol_key = f"CAPITAL_{symbol.upper()}"
            capital_env = os.getenv(symbol_key)
            capital = float(capital_env) if capital_env else usd_amount

        precision = get_precision(symbol)
        qty = round(capital / mark_price, precision)

        print(f"🧾 Ejecutando orden {side} en {symbol} con qty={qty}, TP={tp}, SL={sl}")

        client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY if side.upper() == "BUY" else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=qty,
            positionSide="LONG" if side.upper() == "BUY" else "SHORT"
        )

        colocar_tp_sl(symbol, side, qty, tp, sl)

        confirmar = f"📥 *Orden ejecutada en Binance*\n\n*Activo:* {symbol}\n*Dirección:* {side}\n🎯 *TP:* {tp}\n🛡️ *SL:* {sl}"
        enviar_mensaje_telegram(confirmar)

    except Exception as e:
        print(f"❌ ERROR BINANCE: {e}")
        enviar_mensaje_telegram(f"❌ *Error ejecutando orden:* {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ JSON recibido:", data)

        if not data:
            return {"status": "error", "msg": "JSON inválido"}

        resumen = f"📢 *Alerta de TradingView*\n\n🔹 *Activo:* `{data['symbol']}`\n🔹 *Tipo:* `{data['side']}`\n🔹 *TP 🎯:* `{data['tp']}`\n🔹 *SL 🛡️:* `{data['sl']}`\n🔹 *Capital:* `${data['capital']}`"
        enviar_mensaje_telegram(resumen)

        ejecutar_trade(
            symbol=data["symbol"],
            side=data["side"],
            tp=float(data["tp"]),
            sl=float(data["sl"]),
            capital=float(data["capital"])
        )

        return {"status": "ok"}

    except Exception as e:
        print(f"Error en webhook: {e}")
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
