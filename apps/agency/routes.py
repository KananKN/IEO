
import time
import re
from apps.agency import blueprint
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
from sqlalchemy.dialects import postgresql


read_permission = Permission(RoleNeed("read_agency"))
write_permission = Permission(RoleNeed("write_agency"))
delete_permission = Permission(RoleNeed("delete_agency"))

read_list_product_agency = Permission(RoleNeed("read_list product agency"))
read_list_product = Permission(RoleNeed("read_list product"))


@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def agency():
    datas = AgencyModel.query.all()
    # print(datas)
    return render_template('agency/agency.html', segment='agency' ,datas=datas)

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

@blueprint.route('/create_agency')
@login_required
def create_agency():
    return render_template('agency/agency_create.html', segment='create_agency')
# ----------  ------------------------s@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def user_request():
    datas = FeesModel.query.all()
    # print(datas)
    return render_template('supplier/fees.html', segment='fees' ,datas=datas, )


@blueprint.route('/create_agency_api', methods=['POST'])
def create_agency_api():
    
    ref_code = request.args.get('ref') or request.form.get('referral_code')
    # print(f"➡️ ได้ ref_code: {ref_code}")
    ref_agency = None

    if ref_code:
        ref_agency = AgencyModel.query.filter_by(agency_code=ref_code).first()


    if not ref_agency:
        # ถ้าไม่เจอรหัสที่ส่งมา หรือ ref_code ไม่มี → default เป็นของ IEO
        ref_agency = AgencyModel.query.filter_by(agency_code='IEO').first()
        
    referred_by_id = ref_agency.user_id if ref_agency else None
    # print(f"➡️ referred_by_id: {referred_by_id}")
        
    data = request.form
    print("data:",data)
    type_bank = data.get('account_type')
    bank = data.get('n_bank')
    account_number = data.get('n_accountNumber')
    bank_branch = data.get('n_bankBranch')
    type_bank = data.get('account_type')
    foreign_banks = data.get('foreign_banks')
    swiftCode = data.get('n_swiftCode')
    bank_address = data.get('n_bank_address')
    note = data.get('n_note')
    account_name = data.get('n_accountName')
    foreign_banks_name = data.get('foreign_banks_name')
    
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
            role = RoleModel(name='agency', description='Agency role')
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

        # สร้าง Agency
        prefix = "AGY"
        agency = AgencyModel(
            user_id=user.id,
            address=data.get('address'),
            country=data.get('country'),
            first_name=data.get('first_name') or data.get('fullname'),
            last_name=data.get('last_name') or data.get('lastname'),
            tel=data.get('phone'),
            email=data.get('email'),
            status='approved',  # แก้ typo
            org_type='agency',
            agency_code=generate_code(AgencyModel, prefix),
            referred_by_id=ref_agency.id if ref_agency else None,
            bank=bank,
            account_number=account_number,
            bank_branch=bank_branch,
            type_bank=type_bank,
            foreign_banks=foreign_banks,
            swiftCode=swiftCode,
            bank_address=bank_address,
            note=note,
            account_name=account_name,
            foreign_banks_name=foreign_banks_name,
        )

        db.session.add(agency)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'เกิดข้อผิดพลาด', 'error': str(e)}), 500
    




@blueprint.route("/get_listAgency", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listAgency():
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
        3: AgencyModel.agency_code,         # คอลัมน์ที่ 3 -> username
    }

    
    # ดึงข้อมูลไปแสดงตรงนี้
    # query = db.session.query(UserModel).join(Agency, Agency.user_id == UserModel.id).join(Role, UserModel.role_id == Role.id)
    # query = db.session.query(AgencyModel).filter(AgencyModel.org_type.in_(['agency']))
    query = db.session.query(AgencyModel).filter(
                AgencyModel.org_type == 'agency',
                or_(
                    AgencyModel.flag_delete == False,
                    AgencyModel.flag_delete.is_(None)
                )
            )
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
    if length and length > 0:
        users = query.order_by(column_order).offset(start).limit(length).all()
    else:
        # length = -1 -> show all
        users = query.order_by(column_order).all()
    
    # เก็บ referred_by_id ทั้งหมด
    referred_ids = [user.referred_by_id for user in users if user.referred_by_id]
    referred_users = {}

    if referred_ids:
        # ดึง User ที่เป็นคนแนะนำทั้งหมดมาในครั้งเดียว
        # referred_users_query = UserModel.query.filter(UserModel.id.in_(referred_ids)).all()
        # referred_users = {user.id: f"{user.first_name} {user.last_name}" for user in referred_users_query}
        
        referred_users_query = AgencyModel.query.filter(AgencyModel.id.in_(referred_ids)).all()
        referred_users = {agency.id: f"{agency.first_name} {agency.last_name}" for agency in referred_users_query}

    # ==== จบ Optimize ====
    data = []
    for index, user in enumerate(users):
        if user.referred_by_id and user.referred_by_id in referred_users:
            referred_name = referred_users[user.referred_by_id]
        else:
            referred_name = "IEO"

        data_user = model_to_dict(user) | {
            "username": user.user.username if user.user else '',
        }
        
        data.append({
            "id": index + 1,
            "first_name": user.first_name or '',
            "last_name": user.last_name or '',
            "status": user.status or '',
            "agency_code": user.agency_code or '',
            "referred": referred_name,
            "data_user": data_user, 
        })
    # data = []
    # for index, user in enumerate(users):
    #     if user.referred_by:
    #         referred_name = f"{user.referred_by.first_name}"  # ชื่อบริษัทของคนแนะนำ
    #     else:
    #         referred_name = "IEO"  # ถ้าไม่มีคนแนะนำให้เป็น IEO เลย

    #     data_user = model_to_dict(user) | {
    #         "username": user.user.username if user.user else '',
    #     }
        
    #     data.append({
    #         "id": index + 1,
    #         "first_name": user.first_name or '',
    #         "last_name": user.last_name or '',
    #         "status": user.status or '',
    #         "agency_code": user.agency_code or '',
    #         "referred": referred_name ,
    #         "data_user": data_user, 
    #     })

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })    
    
@blueprint.route('/agency_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def agency_update(id):
    datas = AgencyModel.query.filter_by(id=id).first()
    countrylist = CountryModel.query.all()
    # file_data = FileOrganizationModel.query.filter_by(organization_id  = datas.id).all()
    return render_template('agency/agency_update.html', segment='agency' ,datas=datas,countrylist=countrylist)    


@blueprint.route('/update_agency_api', methods=['POST'])
def update_agency_api():
            
    data = request.form
    print("data:",data)
    id_agency = data.get('id') or None
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    first_name= data.get('fullname')
    last_name=data.get('lastname')
    address=data.get('address')
    country=data.get('country')
    tel=data.get('phone')
    email=data.get('email')
    
    type_bank = data.get('account_type')
    bank = data.get('n_bank')
    account_number = data.get('n_accountNumber')
    bank_branch = data.get('n_bankBranch')
    type_bank = data.get('account_type')
    foreign_banks = data.get('foreign_banks')
    swiftCode = data.get('n_swiftCode')
    bank_address = data.get('n_bank_address')
    note = data.get('n_note')
    account_name = data.get('n_accountName')
    foreign_banks_name = data.get('foreign_banks_name')
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
        thisItem.bank=bank
        thisItem.account_number=account_number
        thisItem.bank_branch=bank_branch
        thisItem.type_bank=type_bank
        thisItem.foreign_banks=foreign_banks
        thisItem.swiftCode=swiftCode
        thisItem.bank_address=bank_address
        thisItem.note=note
        thisItem.account_name=account_name
        thisItem.foreign_banks_name=foreign_banks_name
        
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
@read_list_product_agency.require(http_exception=403)
def list_ProductAgency():
    # datas = ProductAgencyAssociation.query.all()
    datas = ProductAgencyAssociation.query.filter(
        or_(
            ProductAgencyAssociation.flag_delete == False,
            ProductAgencyAssociation.flag_delete.is_(None)
        )
    ).all()
    # for agency in datas:
    #     product_agency = ProductAgencyAssociation.query.filter_by(agency_id=datas.id).first()
    # print(datas)
    # print(datas)
    return render_template('agency/list_ProductAgency.html', segment='list_ProductAgency' ,datas=datas, )

@blueprint.route("/get_list_ProductAgency", methods=["POST"])
@login_required

@read_list_product_agency.require(http_exception=403)
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
    
    # Step 1: Base query หาเฉพาะ agency.id (distinct ก่อน)
    # base_query = db.session.query(Agency.id).\
    #     outerjoin(ProductAgencyAssociation, Agency.id == ProductAgencyAssociation.agency_id).\
    #     outerjoin(Product, Product.id == ProductAgencyAssociation.product_id)

    base_query = (
        db.session.query(Agency.id)
        .outerjoin(ProductAgencyAssociation, Agency.id == ProductAgencyAssociation.agency_id)
        .outerjoin(Product, Product.id == ProductAgencyAssociation.product_id)
        .filter(
            func.coalesce(Agency.flag_delete, False) == False,
            func.coalesce(ProductAgencyAssociation.flag_delete, False) == False,
        )
    )

    if search_value:
        search = f"%{search_value}%"
        base_query = base_query.filter(
            or_(
                Agency.first_name.ilike(search),
                Agency.last_name.ilike(search),
                Agency.country.ilike(search),
                Agency.tel.ilike(search),
                Product.name.ilike(search)
            )
        )



    base_query = base_query.distinct()

    # print("---- SQL FROM base_query ----")
    # print(base_query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

    total_records = db.session.query(Agency.id).distinct().count()
    # filtered_records = base_query.count()

    # Step 2: pagination
    agency_ids = base_query.offset(start).limit(length).all()
    agency_ids = [a.id for a in agency_ids]

    # Step 3: ดึงข้อมูลจริง (Agency + Product)
    # query = db.session.query(Agency, Product.name).\
    #     filter(Agency.id.in_(agency_ids)).\
    #     outerjoin(ProductAgencyAssociation, Agency.id == ProductAgencyAssociation.agency_id).\
    #     outerjoin(Product, Product.id == ProductAgencyAssociation.product_id).\
    #     order_by(Agency.id)
    query = (
        db.session.query(Agency, Product.name)
        .outerjoin(ProductAgencyAssociation, Agency.id == ProductAgencyAssociation.agency_id)
        .outerjoin(Product, Product.id == ProductAgencyAssociation.product_id)
        .filter(
            Agency.id.in_(agency_ids),
            func.coalesce(Agency.flag_delete, False) == False,
            func.coalesce(ProductAgencyAssociation.flag_delete, False) == False,
        )
        .order_by(Agency.id)
    )

    # print("---- SQL FROM final query ----")
    # print(query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


    rows = query.all()

    # Group ข้อมูลตาม employee_id
    grouped = {}
    display_index = start + 1 # 👈 เริ่มนับลำดับที่ 1


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
        if agency["product"]:
            badges = list(sorted(agency["product"]))
            badge_html = ""
            for i, p in enumerate(badges):
                comma = "," if i < len(badges) - 1 else ""
                badge_html += f'<span class="badge bg-info text-white mb-1">{p.strip()}</span>{comma}'
            
            agency["product"] = f'<div class="product-badges">{badge_html}</div>'
        else:
            agency["product"] = "ไม่มีโครงการ"

        data.append(agency)

    # ส่งออกข้อมูล
    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })     
    

@blueprint.route('/delete_agency', methods=['POST'])
@login_required
def delete_agency():
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
    item_Del = AgencyModel.query.get(id_del)

    if item_Del:
        # db.session.delete(item_Del)
        item_Del.flag_delete = True   # 
        db.session.commit()
    
    # db.session.query(AgencyModel).filter(AgencyModel.id == id_del).delete()
    # ProductAgencyAssociation.query.filter_by(agency_id=id_del).delete()
    assoc_items = ProductAgencyAssociation.query.filter_by(agency_id=id_del).all()
    for a in assoc_items:
        a.flag_delete = True

    db.session.commit()
        
    flash(' Deleted!', 'success')
    return redirect(url_for('agency_blueprint.agency'))   