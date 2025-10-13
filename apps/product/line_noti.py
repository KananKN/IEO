import os
import requests
from apps.notification.models import *

def send_line_message(message, config):
    if not config:
        print("❌ ยังไม่ได้ตั้งค่า LINE Token")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {config.channel_access_token}",
        "Content-Type": "application/json"
    }

    target = config.group_id or config.user_id
    payload = {
        "to": target,
        "messages": [{"type": "text", "text": message}]
    }

    print("➡️ Sending payload:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Response status:", response.status_code)
        print("Response text:", response.text)

        response.raise_for_status()
        print("✅ ส่งสำเร็จ:", response.json())
        return True
    except requests.exceptions.RequestException as err:
        print("❌ Error sending message:", err)
        return False

def send_line_message1(message):
    config = LineConfigModel.query.first()
    if not config:
        print("❌ ยังไม่ได้ตั้งค่า LINE Token")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {config.channel_access_token}",
        "Content-Type": "application/json"
    }

    target = config.group_id or config.user_id
    payload = {
        "to": target,
        "messages": [{"type": "text", "text": message}]
    }

    print("➡️ Sending payload:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Response status:", response.status_code)
        print("Response text:", response.text)  # <== สำคัญสุด

        response.raise_for_status()
        print("✅ ส่งสำเร็จ:", response.json())
        return True
    except requests.exceptions.RequestException as err:
        print("❌ Error sending message:", err)
        return False
    
def send_line_message_by_id(config_id, message):
    config = LineConfigModel.query.get(config_id)
    if not config:
        print("❌ ไม่พบ config นี้")
        return False

    target = config.group_id or config.user_id
    if not target:
        print("❌ ไม่มี group_id หรือ user_id")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {config.channel_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": target,
        "messages": [{"type": "text", "text": message}]
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"➡️ Sent to {target}, status: {response.status_code}, text: {response.text}")
    return response.ok




# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# USER_ID =  os.getenv("USER_ID")
# GROUP_ID = os.getenv("LINE_GROUP_ID")  # ID ของกลุ่มที่ต้องการส่งข้อความ

# def send_line_message(message):
#     url = "https://api.line.me/v2/bot/message/push"
#     headers = {
#         "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "to": GROUP_ID,
#         "messages": [
#             {
#                 "type": "text",
#                 "text": message
#             }
#         ]
#     }

#     try:
#         response = requests.post(url, json=payload, headers=headers, timeout=10)
#         response.raise_for_status()
#         print("Sent successfully:", response.json())
#         return response.json()
#     except requests.exceptions.HTTPError as errh:
#         print("HTTP Error:", errh, response.text)
#     except requests.exceptions.RequestException as err:
#         print("Error sending message:", err)