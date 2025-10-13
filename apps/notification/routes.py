
import time
import re
from apps.notification import blueprint
from apps.authentication.models import *
from apps.notification.models import *
from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file
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
from datetime import datetime
import uuid
from sqlalchemy import and_, func, case, asc
from collections import defaultdict

from decimal import Decimal
from apps.product.line_noti import send_line_message_by_id




read_permission = Permission(RoleNeed("read_line"))
write_permission = Permission(RoleNeed("write_line"))
delete_permission = Permission(RoleNeed("delete_line"))


@blueprint.route('/line')
@login_required
@read_permission.require(http_exception=403)
def line():
    # # datas = LineConfigModel.query.all()
    # datas = LineConfigModel.query.filter()
    # # thisItem = ProductCategoryModel.query.filter_by(id=json_data['id']).first()

    
    # print(datas)
    # return render_template('line/line_1.html', segment='line' ,datas=datas)
    try:
        # ✅ ดึงรายการล่าสุด 1 รายการ (ตาม id มากสุด)
        data = LineConfigModel.query.order_by(LineConfigModel.id.desc()).first()
        print("Loaded LINE config:", data.to_dict() if data else "None")    

        if not data:
            flash("ยังไม่มีการตั้งค่า LINE Config", "warning")

        return render_template(
            'line/line_1.html',
            segment='line',
            data=data
        )

    except Exception as e:
        print("❌ Error loading LINE config:", e)
        flash("เกิดข้อผิดพลาดในการโหลดข้อมูล LINE", "danger")
        return render_template('line/line_1.html', segment='line', data=None)


@blueprint.route("/save_line_token", methods=["POST"])
@login_required
def save_line_token():
    data = request.get_json()
    try:
        id = data.get("id")
        name_line = data.get("name_line")
        channel_access_token = data.get("channel_access_token")
        group_id = data.get("group_id")
        # user_id = data.get("user_id")

        if not name_line or not channel_access_token or not group_id:
            return jsonify({"success": False, "message": "กรุณากรอกข้อมูลให้ครบถ้วน"})

        if id:
            # ✅ ถ้ามี id → แก้ไขข้อมูลเดิม
            existing = LineConfigModel.query.get(id)
            if not existing:
                return jsonify({
                    "success": False,
                    "message": "ไม่พบข้อมูลที่ต้องการแก้ไข"
                })

            existing.name = name_line
            existing.channel_access_token = channel_access_token
            existing.group_id = group_id
            # existing.user_id = user_id
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "อัปเดตข้อมูลเรียบร้อยแล้ว"
            })

        else:
            # ✅ ถ้าไม่มี id → เพิ่มใหม่
            new_config = LineConfigModel(
                name=name_line,
                channel_access_token=channel_access_token,
                group_id=group_id,
                # user_id=user_id
            )
            db.session.add(new_config)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "บันทึกข้อมูลใหม่เรียบร้อยแล้ว"
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})


@blueprint.route('/addLine', methods=['POST'])
@login_required
def addLine():
    data = request.get_json()
    print(data)
    name = data.get("name", "").strip()
    channel_access_token = data.get("channel_access_token", "").strip()
    user_id = data.get("user_id", "").strip()
    group_id = data.get("group_id", "").strip()

    if not name:
        return jsonify({"success": False, "message": "กรุณากรอกชื่อบัญชี LINE"}), 400

    # ✅ ตรวจซ้ำชื่อ (กันซ้ำ)
    existing = LineConfigModel.query.filter_by(name=name).first()
    if existing:
        return jsonify({"success": False, "message": "ชื่อบัญชีนี้ถูกใช้แล้ว"}), 409

    newItem = LineConfigModel(name=name, channel_access_token=channel_access_token, user_id=user_id, group_id=group_id)
    db.session.add(newItem)
    db.session.commit()

    # ✅ ส่งข้อความทดสอบหลังบันทึก
    test_result = send_line_message_by_id(newItem.id, "ทดสอบส่งข้อความจากระบบหลังเพิ่มบัญชีใหม่")

    if test_result:
        msg = "บันทึกและส่งข้อความทดสอบสำเร็จ ✅"
    else:
        msg = "บันทึกสำเร็จ แต่ส่งข้อความทดสอบไม่สำเร็จ ⚠️"

    return jsonify({"success": True, "message": msg}), 201



@blueprint.route('/deleteline', methods=['POST'])
@login_required
def deleteline():
    id = request.form.get("id")
    thisItem = LineConfigModel.query.filter_by(id=id).first()

    if not thisItem:
        flash('ไม่พบบัญชี LINE ที่ต้องการลบ', 'danger')
        return redirect(url_for('notification_blueprint.line'))

    db.session.delete(thisItem)
    db.session.commit()
    flash('ลบบัญชี LINE เรียบร้อยแล้ว!', 'success')
    return redirect(url_for('notification_blueprints.line'))

@blueprint.route('/updateLine', methods=['POST'])
@login_required
def updateLine():
    # print(request.form)
    data = request.get_json()

    id = data.get("id")
    name = data.get("name")
    channel_access_token = data.get("channel_access_token")
    user_id = data.get("user_id")
    group_id = data.get("group_id")

    # ✅ ตรวจสอบว่ามี record นี้อยู่จริงไหม
    thisItem = LineConfigModel.query.filter_by(id=id).first()
    if not thisItem:
        return jsonify({"success": False, "message": "ไม่พบบัญชี LINE ที่ต้องการอัปเดต"}), 404

    # ✅ ตรวจสอบชื่อซ้ำ (ยกเว้นตัวเอง)
    duplicate = LineConfigModel.query.filter(
        LineConfigModel.name == name,
        LineConfigModel.id != id
    ).first()
    if duplicate:
        return jsonify({"success": False, "message": "ชื่อบัญชีนี้ถูกใช้แล้ว"}), 409

    # ✅ อัปเดตค่า
    thisItem.name = name
    thisItem.channel_access_token = channel_access_token
    thisItem.user_id = user_id
    thisItem.group_id = group_id

    db.session.commit()

    # ✅ (ออปชัน) ส่งข้อความทดสอบหลังอัปเดต
    test_result = send_line_message_by_id(id, "ทดสอบส่งข้อความหลังอัปเดตบัญชี LINE")

    if test_result:
        msg = "อัปเดตสำเร็จ และส่งข้อความทดสอบเรียบร้อย ✅"
    else:
        msg = "อัปเดตสำเร็จ แต่ส่งข้อความทดสอบไม่สำเร็จ ⚠️"

    return jsonify({"success": True, "message": msg}), 200

@blueprint.route('/test_send', methods=['POST'])
@login_required
def line_test_send():
    data = request.get_json()
    line_id = data.get("id")
    print("ทดสอบส่งข้อความไปยัง ID:", line_id)
    config = LineConfigModel.query.filter_by(id=line_id).first()
    if not config:
        return jsonify({"success": False, "message": "LINE config ไม่พบหรือไม่ active"}), 404

    message = "✅ นี่คือข้อความทดสอบจากระบบ"
    success = send_line_message_by_id(config.id, message)
    return jsonify({"success": success, "message": "ส่งสำเร็จ" if success else "ส่งล้มเหลว"})



   
   




