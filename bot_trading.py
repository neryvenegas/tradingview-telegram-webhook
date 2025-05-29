import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# ENV – load credentials from config.env (Render automatically injects them)
# ---------------------------------------------------------------------------
load_dotenv("config.env")                         # ✅ keep the file outside GitHub
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").split()[0]  # strip inline comments
if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured")

TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ---------------------------------------------------------------------------
# FLASK APP
# ---------------------------------------------------------------------------
app = Flask(__name__)


def send_telegram(text: str) -> dict:
    """Send *text* to Telegram – Markdown‑V2 safe by default."""
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }
    resp = requests.post(TG_API_URL, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


@app.route("/webhook", methods=["POST"])
def webhook():
    """Endpoint that TradingView will hit with a JSON alert body."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        # ────────────────────────────────────────────────────────────────────
        # BUILD A NICE MESSAGE  
        # If the alert already contains a "text" key, forward it as‑is.  
        # Otherwise pretty‑print the whole payload.
        # ────────────────────────────────────────────────────────────────────
        if "text" in data and isinstance(data["text"], str):
            msg = data["text"]
        else:
            msg = "```json\n" + json.dumps(data, indent=2) + "\n```"

        tg_response = send_telegram(msg)
        return jsonify({"status": "ok", "telegram_id": tg_response.get("result", {}).get("message_id")})

    except Exception as exc:
        return jsonify({"status": "error", "detail": str(exc)}), 500


if __name__ == "__main__":
    # Local debugging – not used on Render (Gunicorn will take over)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
