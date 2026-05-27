# ============================================================
#  main.py — LINE Webhook + Gemini AI Intent Matching
# ============================================================

import os
import json
import requests
from google import genai
from flask import Flask, request, abort
from menus import MENUS, MENU_NAMES, MENU_TEXT

app = Flask(__name__)
# v2
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
GEMINI_API_KEY            = os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY)

def reply_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    requests.post(url, headers=headers, json=body)

def detect_menu(user_message):
    menu_list = "\n".join(f"- {name}" for name in MENU_NAMES)
    prompt = f"""คุณคือผู้ช่วยที่ช่วยจับคู่คำถามกับเมนูที่มีอยู่

รายการเมนูที่มีทั้งหมด:
{menu_list}

ผู้ใช้พิมมาว่า: "{user_message}"

คำถาม: ผู้ใช้ต้องการเมนูไหน?
- ตอบแค่ชื่อเมนูเท่านั้น ห้ามมีคำอื่น
- ถ้าไม่ตรงกับเมนูใดเลย ให้ตอบว่า: none
- ถ้าผู้ใช้พิม menu / เมนู / faq / help ให้ตอบว่า: menu"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-8b",
            contents=prompt
        )
        result = response.text.strip()
        print(f"[GEMINI RAW] {result}")
        return result
    except Exception as e:
        print(f"Gemini error: {e}")
        return "none"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    try:
        data = json.loads(body)
    except Exception:
        abort(400)

    events = data.get("events", [])
    for event in events:
        if event.get("type") != "message":
            continue
        if event["message"].get("type") != "text":
            continue

        reply_token  = event["replyToken"]
        user_message = event["message"]["text"].strip()
        print(f"[USER] {user_message}")

        detected = detect_menu(user_message)
        print(f"[AI DETECTED] {detected}")

        if detected == "menu":
            reply_message(reply_token, MENU_TEXT)
        elif detected in MENUS:
            reply_message(reply_token, MENUS[detected]["answer"])
        else:
            reply_message(
                reply_token,
                "ขออภัยครับ ไม่เข้าใจคำถาม 🙏\n"
                "กรุณาพิมพ์ menu หรือ เมนู เพื่อดูรายการที่มีครับ"
            )

    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "LINE Chatbot is running! 🤖", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
