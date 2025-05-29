import os, json, datetime, requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------------
load_dotenv("config.env")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").split()[0]
if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured")

TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
app = Flask(__name__)

_escape_chars = r"_*[]()~`>#+-=|{}.!"
md = lambda t: ''.join(('\\' + c) if c in _escape_chars else c for c in str(t))  # safe MarkdownV2


def fmt_trade(d: dict) -> str:
    side = d.get("side", "?").upper()
    return (
        f"{'🟢' if side=='BUY' else '🔴'} *{md(d.get('symbol'))}*\n"
        f"`{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}`\n"
        f"*{side}* @ _market_\n"
        f"🎯 TP: `{md(d.get('tp'))}`\n"
        f"🛡 SL: `{md(d.get('sl'))}`\n"
        f"💰 Capital: `${md(d.get('capital'))}`"
    )


def send_telegram(text: str):
    resp = requests.post(TG_API_URL, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw = request.get_data(as_text=True) or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"text": raw}

        if {"symbol", "side", "tp", "sl", "capital"}.issubset(data):
            msg = fmt_trade(data)
        else:
            txt = data.get("text", json.dumps(data, indent=2))
            msg = f"```json\n{txt}\n```"

        tg_resp = send_telegram(msg)
        return jsonify(status="ok", id=tg_resp.get("result", {}).get("message_id"))

    except Exception as exc:
        return jsonify(status="error", detail=str(exc)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
