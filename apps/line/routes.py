import time
import re
from apps.line import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.order.models import *
from apps.lead.models import *
from apps.bank_account.models import *

from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, Response, current_app
from flask_login import login_required, current_user, logout_user
from jinja2 import TemplateNotFound
import random
import string
import requests
import base64
from io import BytesIO
from PIL import Image
from flask_principal import Permission, RoleNeed
import json
import os
from datetime import datetime, date, time
from sqlalchemy import and_, func, case, asc, or_, cast, String, desc, text, extract, Date
from sqlalchemy.orm import aliased, joinedload
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler

# ---------------- LINE CONFIG ----------------
LINE_TOKEN = "MxhKW0223Qw9AKWlxwtVnPmv8bIHUQdZgnIrvo5wIVA1gkDrYh7Q8AcrmZUe2W3kwwpAMg+otiBzVGh32oKotEIHZSrpoeR6YS8vmhyj+UiKKjiLT9Z6gzS7cgrlLuWF/g2adrbHRDQb2N/y5+SfwgdB04t89/1O/w1cDnyilFU="
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

def send_line_message(to, message_text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": to,  # groupId หรือ userId
        "messages": [{
            "type": "text",
            "text": message_text
        }]
    }
    r = requests.post(LINE_PUSH_URL, headers=headers, json=payload)
    print(r.status_code, r.text)

def send_line_reply(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    r = requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    print(r.status_code, r.text)

# ---------------- Webhook ----------------
@blueprint.route("/webhook", methods=["POST"])
def line_webhook():
    body = request.get_json()
    print("===== Webhook body =====")
    print(body)
    print("========================")

    for event in body.get("events", []):
        source = event.get("source", {})
        reply_token = event.get("replyToken")

        if source.get("type") == "group":
            group_id = source.get("groupId")
            print(f"📌 ได้ groupId = {group_id}")
            send_line_reply(reply_token, f"GroupId ของกลุ่มนี้คือ:\n{group_id}")

        elif source.get("type") == "user":
            user_id = source.get("userId")
            print(f"📌 ได้ userId = {user_id}")
            send_line_reply(reply_token, f"UserId ของคุณคือ:\n{user_id}")

    return jsonify({"status": "ok"})

# ---------------- Sales Summary ----------------
def send_daily_sales_report():
    with current_app.app_context():
        today = date.today()
        total_sales = (
            db.session.query(func.sum(PaymentModel.amount))
            .filter(func.date(PaymentModel.payment_date) == today)
            .scalar()
        ) or 0

        message = (
            f"📊 รายงานยอดขายประจำวันที่ {today.strftime('%d/%m/%Y')}\n"
            f"💰 ยอดขายรวม: {total_sales:,.2f} บาท"
        )

        group_id = "C3eb0797f9adb9aaaf23fec19e6b0d5f7"
        send_line_message(group_id, message)
        print("[SCHEDULER] ส่งยอดขายเรียบร้อย")

# Route สำหรับกดส่งเอง
@blueprint.route("/send_sales")
def send_sales():
    send_daily_sales_report()
    return "ส่งข้อความเรียบร้อยแล้ว"

# ---------------- Scheduler ----------------
def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(send_daily_sales_report, "cron", hour=9, minute=0)  # ทุกวัน 21:00
    scheduler.start()

    # ป้องกัน scheduler ถูก kill ตอน Flask reload/exit
    import atexit
    atexit.register(lambda: scheduler.shutdown())

# เรียก scheduler ตอน Flask app เริ่ม
@blueprint.record_once
def init_scheduler(setup_state):
    app = setup_state.app
    start_scheduler(app)
