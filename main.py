# ============================================================
#  main.py — LINE Webhook + Gemini AI Intent Matching
# ============================================================

import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, abort
from menus import MENUS, MENU_NAMES, MENU_TEXT

app = Flask(__name__)

# ============================================================
#  ตั้งค่า — ใส่ค่าจริงตรงนี้ หรือตั้งเป็น Environment Variable
# ============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "qi8YydZ0KXlK24h/ApD9fcvJwLgLOKfCgGaQp2KM2kJQjbKZQw502ZNa6Xx+L8UQ9k5i0uwpvQlMPU1BpbX0GDhC7RUKbWOwYDgwAjnYZIkZ0iyjczW/hmr/z392gF50RlHyQsV5Dm0QH+jwGriebgdB04t89/1O/w1cDnyilFU=")
GEMINI_API_KEY            = os.environ.get("GEMINI_API_KEY", "AIzaSyDKp0TyRNF4WUYOP5kd4eOJkCxIu48MqAU")

# ตั้งค่า Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ============================================================
#  ฟังก์ชันส่งข้อความกลับ LINE
# ============================================================
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

# ============================================================
#  ฟังก์ชันให้ AI เดาว่าผู้ใช้ต้องการเมนูไหน
# ============================================================
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
        response = model.generate_content(prompt)
        result = response.text.strip()
        return result
    except Exception as e:
        print(f"Gemini error: {e}")
        return "none"

# ============================================================
#  Webhook endpoint — LINE ส่งข้อความมาที่นี่
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)

    try:
        data = json.loads(body)
    except Exception:
        abort(400)

    events = data.get("events", [])

    for event in events:
        # รับเฉพาะ message event ประเภท text
        if event.get("type") != "message":
            continue
        if event["message"].get("type") != "text":
            continue

        reply_token  = event["replyToken"]
        user_message = event["message"]["text"].strip()

        print(f"[USER] {user_message}")

        # ให้ AI เดาเมนู
        detected = detect_menu(user_message)
        print(f"[AI DETECTED] {detected}")

        if detected == "menu":
            reply_message(reply_token, MENU_TEXT)

        elif detected in MENUS:
            answer = MENUS[detected]["answer"]
            reply_message(reply_token, answer)

        else:
            # ไม่ตรงเมนูใดเลย
            reply_message(
                reply_token,
                "ขออภัยครับ ไม่เข้าใจคำถาม 🙏\n"
                "กรุณาพิมพ์ menu หรือ เมนู เพื่อดูรายการที่มีครับ"
            )

    return "OK", 200

# ============================================================
#  Health check — ใช้เช็คว่า server ทำงานอยู่
# ============================================================
@app.route("/", methods=["GET"])
def index():
    return "LINE Chatbot is running! 🤖", 200

# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)