
import time
import re
from apps.user_request import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.supplier.models import *
from apps import db
from flask import Flask,render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file
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
from sqlalchemy.orm import aliased
from sqlalchemy import and_, func, case, asc, or_
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ตั้งค่าอีเมล
app.config['MAIL_SERVER'] = 'localhost'  # ใช้ MailHog ที่รันบนเครื่อง (localhost)
app.config['MAIL_PORT'] = 1025  # พอร์ตที่ MailHog ใช้
app.config['MAIL_USE_TLS'] = False  # ไม่ต้องใช้ TLS
app.config['MAIL_USE_SSL'] = False  # ไม่ต้องใช้ SSL
app.config['MAIL_USERNAME'] = ''  # ไม่มี username
app.config['MAIL_PASSWORD'] = ''  # ไม่มี password
app.config['MAIL_DEFAULT_SENDER'] = ('IEO Team', 'noreply@ieo.local') 
mail = Mail(app)
# # import logging

# logging.basicConfig(filename='error.log', level=logging.ERROR)

read_permission = Permission(RoleNeed("read_user request"))
write_permission = Permission(RoleNeed("write_user request"))
delete_permission = Permission(RoleNeed("delete_user request"))


# ---------- agency_request ------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = UserModel.query.filter(UserModel.status == 'pending').all()
    roles = RoleModel.query.all()
    # print(datas)
    return render_template('user_request/agency_request.html', segment='agency_request' ,datas=datas, roles=roles)

def model_to_dict(model):
    data = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        if isinstance(value, bytes):  # ตรวจสอบว่าเป็น bytes หรือไม่
            # แปลงเป็น base64 หรือ string
            value = base64.b64encode(value).decode('utf-8')
        data[c.name] = value
    return data

def generate_code(model, prefix):
    last_entry = model.query.order_by(model.id.desc()).first()
    next_id = (last_entry.id + 1) if last_entry else 1
    return f"{prefix}{str(next_id).zfill(5)}"

@blueprint.route("/get_agenctRequest", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_agenctRequest():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    Agency = aliased(AgencyModel)
    Role = aliased(RoleModel)


    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: UserModel.id,               # คอลัมน์ที่ 0 -> id
        1: Agency.first_name,          # คอลัมน์ที่ 1 -> first_name
        2: Agency.last_name,           # คอลัมน์ที่ 2 -> last_name
        3: UserModel.username,         # คอลัมน์ที่ 3 -> username
        4: UserModel.role_id           # คอลัมน์ที่ 4 -> role_id
    }

    
    # ดึงข้อมูลไปแสดงตรงนี้
    # query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id)
    query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id).filter(UserModel.status == 'pending')
        # คำค้นหาจาก DataTable
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                UserModel.username.ilike(search),
                Agency.first_name.ilike(search),
                Agency.last_name.ilike(search),
                Role.name.ilike(search)
            )
        )

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, UserModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = UserModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    users = query.order_by(column_order).offset(start).limit(length).all()

    # แสดง SQL ที่ถูกสร้าง

    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,  # เลขลำดับที่เริ่มจาก 1
        "datass": model_to_dict(user.agency),  # แปลง user ทั้งหมดเป็น dictionary
        "first_name": user.agency.first_name if user.agency else '',
        "last_name": user.agency.last_name if user.agency else '',
        "name": user.username,
        "role": user.role.name if user.role else '',
        "data_user": model_to_dict(user)
    } for index, user in enumerate(users)]  # ไม่ต้อง unpack user อีก

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })

@blueprint.route("/check_statusUser", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def check_statusUser():
    json_data = request.get_json()
    print(json_data)

    id =json_data["id"]
    status =json_data["status"]
    
    check_id = UserModel.query.filter_by(id=id).first()
    
    
    if not check_id:
        print("⚠️ ไม่พบ Username:", check_id)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ไม่พบ Username', "data": check_id}), 400

        
    else:
        thisItem = UserModel.query.filter_by(id=id).first()
        thisItem.status = status
        
        thisAgency = AgencyModel.query.filter_by(user_id=id).first()
        thisAgency.status = status
        
        prefix = "AGY" if thisAgency.org_type == 'agency' else "UNIT"
        new_code = generate_code(AgencyModel, prefix)
        thisAgency.code = new_code
        print(new_code)
            
        db.session.commit()
        flash("success!", "success")
        return jsonify({'status': 'Success', 'message': 'Data has been saved', 'data': {
                'id': thisItem.id,
                'username': thisItem.username,
                'status': thisItem.status,
                # เพิ่ม field อื่นๆ ที่ต้องการส่งกลับ (แต่ห้ามเป็น bytes)
            }}), 200

# ---------- agency_request ------------------------s
@blueprint.route('/list_user')
@login_required
@read_permission.require(http_exception=403)
def list_user():
    datas = interestedUsersModel.query.filter(interestedUsersModel.status == 'pending').all()
    # print(datas)
    return render_template('user_request/user_request.html', segment='user_request' ,datas=datas)



@blueprint.route("/get_userRequest", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_userRequest():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: interestedUsersModel.id,               # คอลัมน์ที่ 0 -> id
        1: interestedUsersModel.first_name,          # คอลัมน์ที่ 1 -> first_name
        2: interestedUsersModel.last_name,           # คอลัมน์ที่ 2 -> last_name
        3: interestedUsersModel.email,         # คอลัมน์ที่ 3 -> username
        4: interestedUsersModel.line_id           # คอลัมน์ที่ 4 -> role_id
    }

    
    # ดึงข้อมูลไปแสดงตรงนี้
    # query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id)
    query = db.session.query(interestedUsersModel).filter(interestedUsersModel.status == 'pending')
        # คำค้นหาจาก DataTable
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
                    or_(
                        interestedUsersModel.first_name.ilike(search),
                        interestedUsersModel.last_name.ilike(search),
                        interestedUsersModel.email.ilike(search),
                        interestedUsersModel.line_id.ilike(search)
                    )
                )
        

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, interestedUsersModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = interestedUsersModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    users = query.order_by(column_order).offset(start).limit(length).all()

    # แสดง SQL ที่ถูกสร้าง

    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,  # เลขลำดับที่เริ่มจาก 1
        "first_name": user.first_name if user.first_name else '',
        "last_name": user.last_name if user.last_name else '',
        "data_user": model_to_dict(user)
    } for index, user in enumerate(users)]  # ไม่ต้อง unpack user อีก

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })        
    

@blueprint.route("/check_appovedUser", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def check_appovedUser():
    json_data = request.get_json()

    id =json_data["id"]
    status =json_data["status"]
    
    check_id = interestedUsersModel.query.filter_by(id=id).first()
    
    
    if not check_id:
        print("⚠️ ไม่พบข้อมูล:", check_id)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ไม่พบข้อมูล', "data": check_id}), 400

    else:
        thisItem = interestedUsersModel.query.filter_by(id=id).first()
        # thisItem.status = 'appoved'
        db.session.commit()
        flash("success!", "success")

        email_sent = False
        try:
            full_name = f"{thisItem.first_name} {thisItem.last_name}"
            msg = Message(
                subject="🔧 MailHog Test",
                sender=("IEO Team", "noreply@ieo.local"), 
                recipients=["test@local.dev"],
                body=f"Hello {full_name},\n\nYour status has been updated to: {status}"
            )
            mail.send(msg)
            email_sent = True
            print("✅ Email sent to test@local.dev")
        except Exception as e:
            print(f"⚠️ Failed to send email: {e}")
        
        return jsonify({
                'status': 'Success',
                'message': f'Data has been saved. Email sent: {email_sent}',
                'data': {
                    'id': thisItem.id,
                    'status': thisItem.status,
                }
            }), 200
        
@blueprint.route('/list_agency')
@login_required
@read_permission.require(http_exception=403)
def list_agency():
    datas = AgencyModel.query.all()
    # print(datas)
    return render_template('user_request/listAgencyAll.html', segment='list_agency' ,datas=datas)


@blueprint.route("/get_listAgenct", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listAgenct():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: AgencyModel.id,               # คอลัมน์ที่ 0 -> id
        1: AgencyModel.first_name,          # คอลัมน์ที่ 1 -> first_name
        2: AgencyModel.last_name,           # คอลัมน์ที่ 2 -> last_name
        3: AgencyModel.email,         # คอลัมน์ที่ 3 -> username
    }

    
    # ดึงข้อมูลไปแสดงตรงนี้
    # query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id)
    query = db.session.query(AgencyModel).filter(AgencyModel.status.in_(['pending', 'rejected','active']))
        # คำค้นหาจาก DataTable
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
                    or_(
                        AgencyModel.first_name.ilike(search),
                        AgencyModel.last_name.ilike(search),
                        AgencyModel.email.ilike(search),
                    )
                )
        

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, AgencyModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = AgencyModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    users = query.order_by(column_order).offset(start).limit(length).all()

    # แสดง SQL ที่ถูกสร้าง

    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,  # เลขลำดับที่เริ่มจาก 1
        "first_name": user.first_name if user.first_name else '',
        "last_name": user.last_name if user.last_name else '',
        "status": user.status if user.status else '',
        "data_user": model_to_dict(user)
    } for index, user in enumerate(users)]  # ไม่ต้อง unpack user อีก

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })        
        
@blueprint.route('/list_userAll')
@login_required
@read_permission.require(http_exception=403)
def list_userAll():
    datas = interestedUsersModel.query.all()
    # print(datas)
    return render_template('user_request/list_user.html', segment='list_userAll' ,datas=datas)


@blueprint.route("/get_listUser", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listUser():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")
    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: interestedUsersModel.id,               # คอลัมน์ที่ 0 -> id
        1: interestedUsersModel.first_name,          # คอลัมน์ที่ 1 -> first_name
        2: interestedUsersModel.last_name,           # คอลัมน์ที่ 2 -> last_name
        3: interestedUsersModel.email,         # คอลัมน์ที่ 3 -> username
    }

    
    # ดึงข้อมูลไปแสดงตรงนี้
    # query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id)
    query = db.session.query(interestedUsersModel).filter(interestedUsersModel.status.in_(['pending', 'rejected','active']))
        # คำค้นหาจาก DataTable
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
                    or_(
                        interestedUsersModel.first_name.ilike(search),
                        interestedUsersModel.last_name.ilike(search),
                        interestedUsersModel.email.ilike(search),
                    )
                )
        

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, interestedUsersModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = interestedUsersModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    users = query.order_by(column_order).offset(start).limit(length).all()

    # แสดง SQL ที่ถูกสร้าง

    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,  # เลขลำดับที่เริ่มจาก 1
        "first_name": user.first_name if user.first_name else '',
        "last_name": user.last_name if user.last_name else '',
        "status": user.status if user.status else '',
        "data_user": model_to_dict(user)
    } for index, user in enumerate(users)]  # ไม่ต้อง unpack user อีก

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })        