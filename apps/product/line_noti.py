import os
import requests


LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID =  os.getenv("USER_ID")
GROUP_ID = os.getenv("LINE_GROUP_ID")  # ID ของกลุ่มที่ต้องการส่งข้อความ

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": GROUP_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print("Sent successfully:", response.json())
        return response.json()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh, response.text)
    except requests.exceptions.RequestException as err:
        print("Error sending message:", err)

