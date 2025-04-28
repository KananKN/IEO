
import time
import re
from apps.univercity import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.supplier.models import *
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
from sqlalchemy import and_, func, case, asc, or_
from sqlalchemy.orm import aliased
from collections import defaultdict


read_permission = Permission(RoleNeed("read_univercity"))
write_permission = Permission(RoleNeed("write_univercity"))
delete_permission = Permission(RoleNeed("delete_univercity"))


@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def univercity():
    datas = interestedUsersModel.query.all()
    # print(datas)
    return render_template('univercity/univercity.html', segment='univercity' ,datas=datas)

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


@blueprint.route('/create_univercity')
@login_required
def create_univercity():
    return render_template('univercity/univercity_create.html', segment='create_univercity')


@blueprint.route('/create_univercity_api', methods=['POST'])
def create_univercity_api():
    # print("➡️ args:", request.args)
    ref_code = request.args.get('ref') or request.form.get('referral_code')
    print(f"➡️ ได้ ref_code: {ref_code}")
    ref_agency = None

    if ref_code:
        ref_agency = AgencyModel.query.filter_by(agency_code=ref_code).first()


    if not ref_agency:
        # ถ้าไม่เจอรหัสที่ส่งมา หรือ ref_code ไม่มี → default เป็นของ IEO
        ref_agency = AgencyModel.query.filter_by(agency_code='IEO').first()
        
    referred_by_id = ref_agency.user_id if ref_agency else None
    print(f"➡️ referred_by_id: {referred_by_id}")
        
    data = request.form
    print("data:",data)
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not password or not confirm_password:
        print("⚠️ กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน")
        return jsonify({'status': 'error', 'message': 'กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน'}), 400

    if password != confirm_password:
        print("⚠️ รหัสผ่านไม่ตรงกัน")
        return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    if UserModel.query.filter_by(username=username).first():
        print("⚠️ Username นี้ถูกใช้งานแล้ว:", username)
        return jsonify({'status': 'error', 'message': 'Username นี้ถูกใช้งานแล้ว', "data": username }), 400

    # แฮชรหัสผ่าน
    # hashed_password = hash_pass(password)

    role = RoleModel.query.filter(RoleModel.name == 'agency').first()
    if not role:
        try:
            role = RoleModel(name='university', description='University role')
            db.session.add(role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Cannot create role', 'error': str(e)}), 400
    
    try:
        # สร้าง User
        user = UserModel(username=username, password=password, role_id=role.id)
        db.session.add(user)
        db.session.flush()  # เพื่อให้ได้ user.id โดยไม่ต้อง commit ก่อน

        nameCompany = AgencyModel.query.filter_by(company_name_th=data.get('name_univer')).first()
    
        if nameCompany :
            print("⚠️ ชื่อมหาวิทยาลัยนี้ถูกใช้งานแล้ว")
            return jsonify({'status': 'error', 'message': 'ชื่อมหาวิทยาลัยนี้ถูกใช้งานแล้ว'}), 400
        
        # สร้าง Agency
        prefix = "UNI"
        agency = AgencyModel(
            user_id=user.id,
            address=data.get('address'),
            country=data.get('country'),
            first_name=data.get('first_name') or data.get('fullname'),
            last_name=data.get('last_name') or data.get('lastname'),
            tel=data.get('phone'),
            email=data.get('email'),
            status='approved',  # แก้ typo
            org_type='univercity',
            agency_code=generate_code(AgencyModel, prefix),
            referred_by_id=ref_agency.user_id if ref_agency else None,
            company_name_th=data.get('name_univer'),
        )

        db.session.add(agency)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'เกิดข้อผิดพลาด', 'error': str(e)}), 500
    




@blueprint.route("/get_listUnivercity", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listUnivercity():
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
    query = db.session.query(AgencyModel).filter(AgencyModel.org_type.in_(['univercity']))
        # คำค้นหาจาก DataTable
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
                    or_(
                        AgencyModel.first_name.ilike(search),
                        AgencyModel.last_name.ilike(search),
                        AgencyModel.email.ilike(search),
                        AgencyModel.tel.ilike(search),
                        AgencyModel.agency_code.ilike(search),
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
    
    # เก็บ referred_by_id ทั้งหมด
    referred_ids = [user.referred_by_id for user in users if user.referred_by_id]
    referred_users = {}

    if referred_ids:
        # ดึง User ที่เป็นคนแนะนำทั้งหมดมาในครั้งเดียว
        referred_users_query = UserModel.query.filter(UserModel.id.in_(referred_ids)).all()
        # referred_users = {user.id: f"{user.first_name} {user.last_name}" for user in referred_users_query}

    # ==== จบ Optimize ====

    data = []
    for index, user in enumerate(users):
        if user.referred_by:
            referred_name = f"{user.referred_by.first_name}"  # ชื่อบริษัทของคนแนะนำ
        else:
            referred_name = "IEO"  # ถ้าไม่มีคนแนะนำให้เป็น IEO เลย

        data_user = model_to_dict(user) | {
    "username": user.user.username if user.user else '',
}
        
        data.append({
            "id": index + 1,
            "first_name": user.first_name or '',
            "last_name": user.last_name or '',
            "status": user.status or '',
            "agency_code": user.agency_code or '',
            "referred": referred_name ,
            "data_user": data_user, 
        })

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })    
    
@blueprint.route('/univercity_create')
@login_required
@read_permission.require(http_exception=403)
def univercity_create():
    datas = AgencyModel.query.all()
    countrylist = CountryModel.query.all()
    # file_data = FileOrganizationModel.query.filter_by(organization_id  = datas.id).all()
    return render_template('univercity/univercity_create.html', segment='univercity' ,datas=datas,countrylist=countrylist)    

@blueprint.route('/univercity_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def univercity_update(id):
    datas = AgencyModel.query.filter_by(id=id).first()
    countrylist = CountryModel.query.all()
    # file_data = FileOrganizationModel.query.filter_by(organization_id  = datas.id).all()
    return render_template('univercity/univercity_update.html', segment='univercity' ,datas=datas,countrylist=countrylist)  


@blueprint.route('/update_univercity_api', methods=['POST'])
def update_univercity_api():
            
    data = request.form
    print("data:",data)
    id_agency = data.get('id') or None
    username = data.get('username')
    company_name_th = data.get('name_univer')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    first_name= data.get('fullname')
    last_name=data.get('lastname')
    address=data.get('address')
    country=data.get('country')
    tel=data.get('phone')
    email=data.get('email')
        #     email=data.get('email'),


    if password != confirm_password:
        print("⚠️ รหัสผ่านไม่ตรงกัน")
        return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    # แฮชรหัสผ่าน
    # hashed_password = hash_pass(password)
    
    try:
                       
        thisItem = AgencyModel.query.filter_by(id=id_agency).first()
        if not thisItem:
            return jsonify({'status': 'error', 'message': 'ไม่พบ Agency ที่ต้องการแก้ไข'}), 404

        # ตรวจสอบชื่อซ้ำ
        if first_name != thisItem.first_name:
            name_check = AgencyModel.query.filter(AgencyModel.first_name == first_name, AgencyModel.id != thisItem.id).first()
            if name_check:
                return jsonify({'status': 'error', 'message': 'ชื่อซ้ำกับในระบบ'}), 400

        if last_name != thisItem.last_name:
            name_check = AgencyModel.query.filter(AgencyModel.last_name == last_name, AgencyModel.id != thisItem.id).first()
            if name_check:
                return jsonify({'status': 'error', 'message': 'นามสกุลซ้ำกับในระบบ'}), 400

        # อัปเดตข้อมูล Agency
        thisItem.first_name = first_name
        thisItem.last_name = last_name
        thisItem.address = address
        thisItem.country = country
        thisItem.tel = tel
        thisItem.email = email
        thisItem.company_name_th = company_name_th
        
        # สร้าง User
        thisUser = UserModel.query.filter_by(id=thisItem.user_id).first()
        if not thisUser:
            return jsonify({'status': 'error', 'message': 'ไม่พบ User ที่เกี่ยวข้อง'}), 404

        if password:
            thisUser.password = hash_pass(password)

        db.session.commit()

        return jsonify({'status': 'success', 'message': 'แก้ไขข้อมูลสำเร็จ'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'เกิดข้อผิดพลาด', 'error': str(e)}), 500
    

@blueprint.route('/list_ProductAgency')
@login_required
@read_permission.require(http_exception=403)
def list_ProductAgency():
    datas = AgencyModel.query.all()
    # for agency in datas:
    #     product_agency = ProductAgencyAssociation.query.filter_by(agency_id=datas.id).first()
    print(datas)
    # print(datas)
    return render_template('agency/list_ProductAgency.html', segment='list_ProductAgency' ,datas=datas, )

@blueprint.route("/get_list_ProductAgency", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_list_ProductAgency():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    Product = aliased(ProductForSalesModel)
    Agency = aliased(AgencyModel)
    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: Agency.id,          # คอลัมน์ที่ 0 -> id
        1: Agency.first_name,        # คอลัมน์ที่ 1 -> name
        2: Agency.country,  # คอลัมน์ที่ 2 -> description
        3: Agency.tel,         # คอลัมน์ที่ 3 -> tel
        4: Product.name          # คอลัมน์ที่ 4 -> product
    }
    
    # ค้นหาข้อมูล
    query = db.session.query(Agency, Product.name).\
    outerjoin(ProductAgencyAssociation, Agency.id == ProductAgencyAssociation.agency_id).\
    outerjoin(Product, Product.id == ProductAgencyAssociation.product_id).\
    outerjoin(CountryModel, CountryModel.id == Agency.country_id)


    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                Agency.first_name.ilike(search),
                Agency.country.ilike(search),
                Agency.tel.ilike(search),
                Product.name.ilike(search)
            )
        )

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, Agency.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
        query = query.order_by(column_order)
    else:
        query = query.order_by(Agency.id)

    # Pagination
    total_records = query.count()
    query = query.offset(start).limit(length)
    rows = query.all()

    # Group ข้อมูลตาม employee_id
    grouped = {}
    display_index = 1  # 👈 เริ่มนับลำดับที่ 1


    for index, (agency, product_name) in enumerate(rows,start=start):
        agency_id = agency.id

        if agency_id not in grouped:
            grouped[agency_id] = {
                "id": display_index ,
                "data_id": agency.id,
                "first_name": agency.first_name,
                "last_name": agency.last_name,
                "country": agency.country,
                "agency_code": agency.agency_code,
                "tel": agency.tel,
                "product": set()
            }
            display_index += 1 
        if product_name:
            grouped[agency_id]["product"].add(product_name)

    # แปลง set → string และแสดงผลเป็น badge
    data = []
    for agency in grouped.values():
        # สร้าง badge สำหรับแต่ละ product
        agency["product"] = ', '.join(
            [f'<span class="badge bg-info text-white me-1">{p.strip()}</span>' for p in sorted(agency["product"])]
        ) if agency["product"] else "ไม่มีโครงการ"

        data.append(agency)

    # ส่งออกข้อมูล
    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })  
    

@blueprint.route('/delete_univercity', methods=['POST'])
@login_required
def delete_univercity():
    id_del = request.form["id"]

    
    # file_list = FileSupplierModel.query.filter_by(supplier_id=id_del).all()

    # for file_item in file_list:
    #     if file_item.file_type == 1:
    #         try:
    #             file_path = os.path.join("apps", "static", "assets", "files", "supplier", file_item.filename)
    #             os.remove(file_path)
    #         except FileNotFoundError:
    #             print(f"❌ ไม่พบไฟล์: {file_path}")
    #         except Exception as e:
    #             print(f"⚠️ เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
    # thisFile.flag_delete = True
    db.session.query(AgencyModel).filter(AgencyModel.id == id_del).delete()
    ProductAgencyAssociation.query.filter_by(agency_id=id_del).delete()

    db.session.commit()
        
    flash(' Deleted!', 'success')
    return redirect(url_for('univercity_blueprint.univercity'))   