from datetime import date
from sqlalchemy import func
from your_models import PaymentModel, db  # ปรับตามไฟล์โมเดลจริง
import requests
import os

# --- ฟังก์ชันส่ง LINE ---
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")  # Channel Access Token ของ OA

def send_line_message(to, message_text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": to,
        "messages": [{"type": "text", "text": message_text}]
    }
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
    print("LINE push status:", r.status_code, r.text)

# --- ฟังก์ชันดึงยอดขายรายเดือน ---
def get_monthly_sales(year, month):
    total_sales = db.session.query(func.sum(PaymentModel.amount))\
        .filter(func.extract('year', PaymentModel.created_at) == year)\
        .filter(func.extract('month', PaymentModel.created_at) == month)\
        .scalar() or 0.0
    return total_sales

# --- main code ---
if __name__ == "__main__":
    year = 2025
    month = 7
    total_sales = get_monthly_sales(year, month)

    message = (
        f"📊 รายงานยอดขายประจำเดือน {month}/{year}\n"
        f"💰 ยอดขายรวม: {total_sales:,.2f} บาท"
    )

    group_id = "Cxxxxxxxxxxxxxxxx"  # ใส่ groupId ของคุณ
    send_line_message(group_id, message)
