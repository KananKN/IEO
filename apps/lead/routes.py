
import time
import re
from apps.lead import blueprint
from apps.authentication.models import *
from apps.organization.models import *
from apps.product.models import *
from apps.supplier.models import *
from apps.employee.models import *
from apps.coordinator.models import *
from apps.order.models import *
from apps.lead.models import *
from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, has_request_context, Response
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
from sqlalchemy import and_, func, case, asc, or_, cast, String
from sqlalchemy.orm import aliased
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound




# import logging

# logging.basicConfig(filename='error.log', level=logging.ERROR)

read_permission = Permission(RoleNeed("read_lead"))
write_permission = Permission(RoleNeed("write_lead"))
delete_permission = Permission(RoleNeed("delete_lead"))

def model_to_dict(model):
    data = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        if isinstance(value, bytes):  # ตรวจสอบว่าเป็น bytes หรือไม่
            # แปลงเป็น base64 หรือ string
            value = base64.b64encode(value).decode('utf-8')
        data[c.name] = value
    return data

def convert_timestamp_to_date(dt):
    if isinstance(dt, datetime):
        # print(dt)
        return dt.strftime('%d/%m/%Y')
    return ''

def safe_model_to_dict(model):
    result = {}
    for column in model.__table__.columns:
        val = getattr(model, column.name)
        if isinstance(val, str):
            # Escape all control characters
            val = val.replace("\\", "\\\\") \
                     .replace("\n", "\\n") \
                     .replace("\r", "\\r") \
                     .replace("\t", "\\t") \
                     .replace('"', '\\"')
        result[column.name] = val
    return result

def generate_member_code():
    year_month = datetime.now().strftime("%Y%m")
    prefix = f"MB{year_month}"

    # ดึงรหัสล่าสุดที่ขึ้นต้นด้วย prefix
    latest_member = db.session.query(MemberModel.member_code)\
        .filter(MemberModel.member_code.like(f"{prefix}%"))\
        .order_by(MemberModel.member_code.desc()).first()

    if latest_member and latest_member[0]:
        last_number = int(latest_member[0][len(prefix):])  # ตัด prefix ออกเพื่อเอาเลข
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{str(next_number).zfill(5)}"

# ---------- Fees ------------------------s
@blueprint.route('/api/get_countries_by_category/ ')
@login_required
@read_permission.require(http_exception=403)
def get_countries_by_category():
    category = ProductCategoryModel.query.get_or_404(category_id)
    
    # ดึงข้อมูลประเทศที่เกี่ยวข้องกับหมวดหมู่นี้
    countries = CountryModel.query.filter_by(category_id=category.id).all()
    
    # ดึงข้อมูลโครงการที่เกี่ยวข้องกับหมวดหมู่นี้
    projects = ProductForSalesModel.query.filter_by(category_id=category.id).all()
    
    # สร้างลิสต์ของประเทศและโครงการที่ต้องการส่งกลับ
    country_list = [{"id": country.id, "name": country.name} for country in countries]
    project_list = [{"id": project.id, "name": project.name} for project in projects]
    
    # ส่งข้อมูลกลับเป็น JSON
    return jsonify({
        "category": {"id": category.id, "name": category.name},
        "countries": country_list,
        "projects": project_list
    })

@blueprint.route("/get_product_list")
def get_product_list():
    products = ProductForSalesModel.query.all()
    result = [{"id": p.id, "name": p.name} for p in products]
    return jsonify(result)

@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def lead_list():
    datas = leadModel.query.all()

    category = ProductCategoryModel.query.all()
    country = CountryModel.query.all()
    
    product = ProductForSalesModel.query.all()
    agencies = AgencyModel.query.all()

    social_channels = [
        {"id": 1, "name": "Facebook"},
        {"id": 2, "name": "Instagram"},
        {"id": 3, "name": "YouTube"},
        {"id": 4, "name": "TikTok"},
        {"id": 5, "name": "Line"},
        {"id": 6, "name": "Twitter (X)"},
        {"id": 7, "name": "Threads"},
        {"id": 8, "name": "LinkedIn"},
        {"id": 9, "name": "Pinterest"},
        {"id": 10, "name": "อื่น ๆ"},
    ]
    # agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    # agencies_with_IEO.append({'id': None, 'agency_code': 'IEO'})
    agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    agencies_with_IEO.append({
        'id': None,
        'agency_code': 'IEO',
        'first_name': 'IEO',
        'last_name': '',
    })

    # print(datas)
    return render_template('lead/lead_list.html', segment='lead' ,datas=datas,categorys=category,countrys=country,products=product,agencys=agencies,social_channels=social_channels )


def convert_thai_to_date(thai_date_str):
    # แปลง พ.ศ. เป็น ค.ศ.
    day, month, year_th = thai_date_str.split("/")
    year = int(year_th) - 543  # เปลี่ยนจาก พ.ศ. เป็น ค.ศ.
    
    # สร้างเป็นวันที่ในรูปแบบ datetime
    return datetime(year, int(month), int(day))

@blueprint.route("/get_userRequest", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_userRequest():
    request_data = request.get_json()
    product_id = request_data.get("product_id")  # รับจาก dropdown

    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: leadModel.id,
        1: leadModel.first_name,
        2: leadModel.email,
        3: leadModel.tel,
        4: ProductForSalesModel.name,
        5: LeadProgram.year,
        6: AgencyModel.first_name,
        7: LeadProgram.created_at,
        8: leadModel.status,
    }

    query = db.session.query(LeadProgram) \
        .outerjoin(leadModel, LeadProgram.lead_id == leadModel.id) \
        .join(ProductForSalesModel, LeadProgram.product_id == ProductForSalesModel.id) \
        .outerjoin(AgencyModel, LeadProgram.agency_id == AgencyModel.id) \
        .filter(LeadProgram.status.in_(['new', 'contacted', 'pending']))
    
    if product_id:
        query = query.filter(LeadProgram.product_id == product_id)
        
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                leadModel.first_name.ilike(search),
                leadModel.last_name.ilike(search),
                leadModel.email.ilike(search),
                ProductForSalesModel.name.ilike(search),
                AgencyModel.first_name.ilike(search),
                func.to_char(leadModel.created_at, 'DD-MM-YYYY').ilike(search),
                leadModel.status.ilike(search),
            )
        )   

    # การจัดเรียง
    if order:
        column_index = int(order[0]["column"])
        sort_direction = order[0]["dir"]
        column_order = column_map.get(column_index, leadModel.id)

        if sort_direction == "desc":
            column_order = column_order.desc()
        else:
            column_order = column_order.asc()
    else:
        column_order = leadModel.id.asc()

    total_records = query.count()

    programs = query.order_by(column_order).offset(start).limit(length).all()

    data = []
    for index, program in enumerate(programs):
        lead = program.lead
        product = program.product
        agency = program.agency
        agency_name = "IEO" if agency is None else f"{agency.first_name or ''} {agency.last_name or ''}".strip()

        data_list = safe_model_to_dict(program)

        data.append({
            "id": start + index + 1, 
            "first_name": lead.first_name or '',
            "last_name": lead.last_name or '',
            "product_name": product.name if product else '',
            "product_id": product.id if product else '',
            "price": product.price if product else '',
            "category": product.product_category_id if product else '',
            "country": product.country.id if product.country else '',
            "agency": agency_name,
            "email": lead.email or '',
            "tel": lead.tel or '',
            "product": safe_model_to_dict(product) if product else {},
            "lead": safe_model_to_dict(lead) if lead else {},
            "created_at": int(program.created_at.timestamp() * 1000),
            "data_list": data_list
        })

    return Response(
        json.dumps({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data
        }, ensure_ascii=False, default=str),
        content_type="application/json"
    )



@blueprint.route("/check_statusLead", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def check_statusLead():
    json_data = request.get_json()
    print(json_data)
    id_lead =json_data["id"]

    status =json_data["status"]
    remask =json_data["remask"]
    id_pd =json_data["id_pd"]
    product_id_value =json_data["product_id"]
    first_name =json_data["first_name"]
    last_name =json_data["last_name"]
    first_nameEN =json_data["first_nameEN"]
    last_nameEN =json_data["last_nameEN"]
    year =json_data["year"]
    nickname =json_data["nickname"]
    email =json_data["email"]
    tel =json_data["tel"]
    social =json_data["social"]
    category_id =json_data["category_id"]
    country_id =json_data["country_id"]
    gender =json_data["gender"]
    line_id =json_data["line_id"]
    address =json_data["address"]

    agency_id = json_data.get("agency_id")
    if agency_id == 'None' or agency_id == '':
        agency_id = None
        
    # birth_date_raw = json_data.get('birth_date')
    # if birth_date_raw:
    #     try:
    #         # ลองแปลงก่อนทั้งแบบมี '/' และ '-'
    #         birth_date_str = birth_date_raw.replace('/', '-')
    #         birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y")
    #     except ValueError:
    #         birth_date = None  # หาก format ผิด
    # else:
    #     birth_date = None

   
  
    lead = leadModel.query.filter(
            or_(
                leadModel.email == email,
                leadModel.tel == tel  # หรือจะเปลี่ยนชื่อเป็น `tel` ด้วยก็ได้
            )).first()
    product = ProductForSalesModel.query.filter_by(id=product_id_value).first()
    

    # return
    if not lead:
        print("⚠️ ไม่พบข้อมูล:", lead)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ไม่พบข้อมูล', "data": lead}), 400

    else:
        thisItem = leadModel.query.filter_by(id=lead.id).first()
        
        thisItem.first_name=first_name
        thisItem.last_name=last_name
        thisItem.first_nameEN=first_nameEN
        thisItem.last_nameEN=last_nameEN
        thisItem.year=year
        thisItem.nickname=nickname
        thisItem.email=email
        thisItem.tel=tel
        thisItem.agency_id=agency_id
        thisItem.social=social
        thisItem.category_id=category_id
        thisItem.country_id=country_id
        thisItem.product_id=product.id
        thisItem.gender=gender
        thisItem.line_id=line_id
        thisItem.address=address


        
        thisProgram = LeadProgram.query.filter_by(
                        lead_id=int(id_lead),
                        product_id=int(id_pd)
                    ).first()
        

        existing_order = None
        current_year = datetime.utcnow().year
        # print("current_year", current_year)
        if status == 'converted':
            existing_order = db.session.query(OrderModel).filter(
                            OrderModel.lead_id == int(id_lead),
                            OrderModel.status.notin_(['completed', 'cancelled']),
                            # db.extract('year', OrderModel.created_at) == current_year
                        ).first()

        # === จัดการ LeadProgram ===
        if thisProgram:
            # แก้ไขข้อมูลเดิม
            thisProgram.product_id = product.id
            thisProgram.agency_id = agency_id
            thisProgram.remask = remask
            thisProgram.year = year
            thisProgram.updated_at = datetime.utcnow()

            # เปลี่ยนสถานะเฉพาะเมื่อไม่มีออร์เดอร์ที่ยังไม่จบ
            if not existing_order:
                thisProgram.status = status
            else:
                print("⚠️ มีออร์เดอร์ปีเดียวกันที่ยังไม่จบ -> ไม่เปลี่ยนสถานะ LeadProgram")
        else:
            # สร้างใหม่
            new_program = LeadProgram(
                lead_id=lead.id,
                product_id=product.id,
                agency_id=agency_id,
                status=status if not existing_order else 'new',
                remask=remask,
                year=year
            )
            db.session.add(new_program)

        # Commit การเปลี่ยนแปลงของ LeadProgram
        db.session.commit()

        # ถ้ามีออร์เดอร์ค้างปีเดียวกัน และสถานะเป็น 'converted' => ห้ามสร้างใหม่
        if existing_order:
            print("⚠️ พบออร์เดอร์ปีเดียวกันที่ยังไม่จบ ไม่สามารถสร้างใหม่ได้")
            return jsonify({
                "status": "error",
                "message": "ไม่สามารถสร้างออร์เดอร์ได้ เนื่องจากมีออร์เดอร์ที่ยังไม่จบในปีเดียวกัน"
            }), 500

        # === ถ้า status เป็น 'converted' ให้สร้าง Order ใหม่ ===
        if status == 'converted':
            try:
                # ตรวจสอบว่า Member เคยมีหรือไม่
                existing_member = MemberModel.query.filter(
                    (MemberModel.phone == lead.tel) | (MemberModel.email == lead.email)
                ).first()

                if existing_member:
                    # 🔁 อัปเดตข้อมูลจาก lead ลง member เดิม
                    existing_member.first_name = lead.first_name
                    existing_member.last_name = lead.last_name
                    existing_member.first_nameEN = lead.first_nameEN
                    existing_member.last_nameEN = lead.last_nameEN
                    existing_member.nick_name = lead.nickname
                    existing_member.phone = lead.tel
                    existing_member.email = lead.email
                    existing_member.gender = lead.gender
                    existing_member.line_id = lead.line_id
                    existing_member.address = lead.address

                    new_member = existing_member
                    print(f"🔁 พบ Member เดิม: {existing_member.id} และอัปเดตข้อมูลเรียบร้อย")
                else:
                    new_member = MemberModel(
                        first_name=lead.first_name,
                        last_name=lead.last_name,
                        first_nameEN=lead.first_nameEN,
                        last_nameEN=lead.last_nameEN,
                        nick_name=lead.nickname,
                        phone=lead.tel,
                        email=lead.email,
                        gender=lead.gender,
                        line_id=lead.line_id,
                        address=lead.address,
                        status='pending',
                        approved_by=None,
                        approved_at=None,
                        member_code=generate_member_code()
                    )
                    db.session.add(new_member)

                # สร้างคำสั่งซื้อใหม่
                new_order = OrderModel(
                    note="",
                    order_number=None,
                    payment_method="cash",
                    status="pending",
                    price=product.price,
                    lead_id=lead.id,
                    product_id=product.id,
                    member_id=new_member.id,
                    agency_id=lead.agency_id,
                    year=lead.year,
                    total_price=product.price,
                    discount=0.00,
                    net_price=product.price,
                )
                db.session.add(new_order)
                db.session.commit()

                year_month = datetime.now().strftime("%Y%m")
                order_number = f"{year_month}-{str(new_order.id).zfill(5)}"
                new_order.order_number = order_number
                db.session.commit()

                # เพิ่มสินค้าในคำสั่งซื้อ
                new_item = OrderItemModel(
                    product_id=product.id,
                    product_name=product.name,
                    order_id=new_order.id,
                    order_number=order_number,
                    unit_price=product.price
                )
                db.session.add(new_item)
                db.session.commit()
                print("✅ สร้าง Order สำเร็จ")

                # ✅ ดึงงวดการผ่อนจาก installmentsPaymentModel
                payment_plans = installmentsPaymentModel.query.filter(
                    installmentsPaymentModel.product_for_sales_id == product.id,
                    installmentsPaymentModel.year == str(product.year)
                ).order_by(installmentsPaymentModel.id).all()

                print(payment_plans)
                # ✅ วนลูปสร้าง OrderTermModel ตามงวด
                for i, plan in enumerate(payment_plans, start=1):
                    term = OrderTermModel(
                        order_id=new_order.id,
                        term_detail=plan.term_detail,
                        amount=Decimal(plan.amount),
                        sequence=i,  # ลำดับงวดที่ 1, 2, 3,...
                        discount=0.00,
                        net_price=Decimal(plan.amount),
                        outstanding_amount=Decimal(plan.amount),
                        created_at=datetime.utcnow(),
                        check_vat = plan.check_vat

                    )
                    db.session.add(term)
                db.session.commit()
                print("✅ สร้าง payment_plans สำเร็จ")
                return jsonify({
                    'status': 'Success',
                    'message': 'บันทึกข้อมูลและสร้างคำสั่งซื้อเรียบร้อยแล้ว',
                    'data': {
                        'order_id': new_order.id,
                        'order_number': new_order.order_number,
                        'member_id': new_member.id
                    }
                }), 200

            except Exception as e:
                db.session.rollback()
                print("❌ สร้าง Order ไม่สำเร็จ:", e)
                return jsonify({"status": "error", "message": "ไม่สามารถสร้างคำสั่งซื้อได้"}), 500

        else:
            # ถ้าไม่ใช่ converted => อัปเดตสถานะของ Order ที่มีให้เป็น cancelled
            thisOrder = OrderModel.query.filter_by(lead_id=lead.id, product_id=product.id).first()
            if thisOrder:
                thisOrder.status = 'cancelled'
                db.session.commit()

            return jsonify({
                'status': 'Success',
                'message': 'บันทึกข้อมูลเรียบร้อยแล้ว (ไม่มีการสร้าง Order)',
                'data': {
                    'lead_id': lead.id,
                    'status': status
                }
            }), 200


@blueprint.route("/create_lead")
@login_required
@read_permission.require(http_exception=403)
def create_lead():
    datas = leadModel.query.all()
    category = ProductCategoryModel.query.all()
    country = CountryModel.query.all()
    
    product = ProductForSalesModel.query.all()
    # agencies = AgencyModel.query.filter_by(org_type='agency').order_by(AgencyModel.first_name.asc()).all()
    agencies = AgencyModel.query.filter_by(org_type='agency').order_by(AgencyModel.first_name.asc()).all()
    agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    agencies_with_IEO.append({
        'id': None,
        'agency_code': 'IEO',
        'first_name': 'IEO',
        'last_name': '',
    })

    social_channels = [
        {"id": 1, "name": "Facebook"},
        {"id": 2, "name": "Instagram"},
        {"id": 3, "name": "YouTube"},
        {"id": 4, "name": "TikTok"},
        {"id": 5, "name": "Line"},
        {"id": 6, "name": "Twitter (X)"},
        {"id": 7, "name": "Threads"},
        {"id": 8, "name": "LinkedIn"},
        {"id": 9, "name": "Pinterest"},
        {"id": 10, "name": "อื่น ๆ"},
    ]

    # เพิ่มข้อความ "IEO" ให้กับข้อมูลที่ส่งไปยังหน้าเว็บ
    agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    # agencies_with_IEO.append({
    #     'id': None,
    #     'agency_code': 'IEO',
    #     'first_name': 'IEO',
    #     'last_name': '',
    # })
    return render_template('lead/lead_create.html', segment='create_lead' ,datas=datas,categorys=category,countrys=country, agencys=agencies_with_IEO,product=product,social_channels=social_channels )

@blueprint.route("/follow_lead")
@login_required
@read_permission.require(http_exception=403)
def follow_lead():
    datas = leadModel.query.all()
    category = ProductCategoryModel.query.all()
    country = CountryModel.query.all()
    agencies = AgencyModel.query.all()
    product = ProductForSalesModel.query.all()

    social_channels = [
        {"id": 1, "name": "Facebook"},
        {"id": 2, "name": "Instagram"},
        {"id": 3, "name": "YouTube"},
        {"id": 4, "name": "TikTok"},
        {"id": 5, "name": "Line"},
        {"id": 6, "name": "Twitter (X)"},
        {"id": 7, "name": "Threads"},
        {"id": 8, "name": "LinkedIn"},
        {"id": 9, "name": "Pinterest"},
        {"id": 10, "name": "อื่น ๆ"},
    ]

    # เพิ่มข้อความ "IEO" ให้กับข้อมูลที่ส่งไปยังหน้าเว็บ
    agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    agencies_with_IEO.append({'id': None, 'agency_code': 'IEO'})
    # print(datas)
    return render_template('lead/follow_lead.html', segment='follow_lead' ,datas=datas,categorys=category,countrys=country, agencys=agencies_with_IEO,product=product,social_channels=social_channels)


@blueprint.route("/get_followStatus", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_followStatus():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: leadModel.id,
        1: leadModel.first_name,
        2: leadModel.last_name,
        3: ProductForSalesModel.name,
        4: CountryModel.name,
        5: CountryModel.name,
        6: leadModel.created_at
    }

    query = db.session.query(LeadProgram) \
        .outerjoin(leadModel, LeadProgram.lead_id == leadModel.id) \
        .join(ProductForSalesModel, LeadProgram.product_id == ProductForSalesModel.id) \
        .outerjoin(AgencyModel, LeadProgram.agency_id == AgencyModel.id) 
    
    print("testttt")
    # query = db.session.query(leadModel) \
    # .join(ProductForSalesModel, leadModel.product_id == ProductForSalesModel.id) \
    # .outerjoin(AgencyModel, leadModel.agency_id == AgencyModel.id)
    
  
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                leadModel.first_name.ilike(search),
                leadModel.last_name.ilike(search),
                leadModel.email.ilike(search),
                ProductForSalesModel.name.ilike(search),
                AgencyModel.first_name.ilike(search),
                func.to_char(leadModel.created_at, 'DD-MM-YYYY').ilike(search),
                leadModel.status.ilike(search),
            )
        )   

    # การจัดเรียง
    if order:
        column_index = int(order[0]["column"])
        sort_direction = order[0]["dir"]
        column_order = column_map.get(column_index, leadModel.id)

        if sort_direction == "desc":
            column_order = column_order.desc()
        else:
            column_order = column_order.asc()
    else:
        column_order = leadModel.id.asc()

    total_records = query.count()

    # programs = query.order_by(column_order).offset(start).limit(length).all()

    # data = []
    # for index, program in enumerate(programs):
    #     lead = program.lead
    #     product = program.product
    #     agency = program.agency
    #     agency_name = "IEO" if agency is None else f"{agency.first_name or ''} {agency.last_name or ''}".strip()

    #     data_list = safe_model_to_dict(program)

    #     data.append({
    #         "id": index + 1,
    #         "first_name": lead.first_name or '',
    #         "last_name": lead.last_name or '',
    #         "product_name": product.name if product else '',
    #         "product_id": product.id if product else '',
    #         "price": product.price if product else '',
    #         "category": product.product_category_id if product else '',
    #         "country": product.country_id if product.country else '',
    #         "agency": agency_name,
    #         "created_at": int(user.created_at.timestamp() * 1000),
    #         "data_user": model_to_dict(user)
    #     })

    programs = query.order_by(column_order).offset(start).limit(length).all()

    data = []
    for index, program in enumerate(programs):
        lead = program.lead
        product = program.product
        agency = program.agency
        agency_name = "IEO" if agency is None else f"{agency.first_name or ''} {agency.last_name or ''}".strip()

        data_list = safe_model_to_dict(program)

        data.append({
            "id": start + index + 1, 
            "first_name": lead.first_name or '',
            "last_name": lead.last_name or '',
            "product_name": product.name if product else '',
            "product_id": product.id if product else '',
            "price": product.price if product else '',
            "category": product.product_category_id if product else '',
            "country": product.country_id if product.country else '',
            "agency": agency_name,
            "email": lead.email or '',
            "tel": lead.tel or '',
            "product": safe_model_to_dict(product) if product else {},
            "lead": safe_model_to_dict(lead) if lead else {},
            "created_at": int(program.created_at.timestamp() * 1000),
            "data_list": data_list
        })



    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })

@blueprint.route("/create_order", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def create_order():
    json_data = request.get_json()

    lead_id = json_data["id"]
    product_id_value = json_data["product_id"]
    status = json_data["status"]

    

    lead = leadModel.query.filter_by(id=lead_id).first()
    product = ProductForSalesModel.query.filter_by(id=product_id_value).first()
    # print(status)

    if status is None or status.strip().lower() != "approved":
        return jsonify({
            'status': 'Error',
            'message': 'ไม่สามารถสร้าง Order ได้ ต้องเป็นสถานะ "ปิดการขาย" (approved) เท่านั้น',
            'data': model_to_dict(lead)
        }), 400

    if not lead or not product:
        return jsonify({'status': 'Error', 'message': 'ไม่พบข้อมูล lead หรือ product'}), 400


    
    # อัปเดตสถานะ lead
    lead.status = status
    db.session.commit()

    new_order = OrderModel(
        note="",
        order_number=None,
        payment_method="cash",
        status="pending",
        total_price=product.price,
        lead_id=lead.id,
        product_id=product.id
    )

    db.session.add(new_order)
    db.session.commit()

    year_month = datetime.now().strftime("%Y%m")
    order_number = f"{year_month}-{str(new_order.id).zfill(5)}"  # เช่น 202505-00001

    new_order.order_number = order_number
    db.session.commit()

    return jsonify({
        'status': 'Success',
        'message': 'สร้างคำสั่งซื้อสำเร็จ',
        'data': {
            'id': new_order.id,
            'order_number': new_order.order_number,
            'status': new_order.status
        }
    }), 200



@blueprint.route('/delete_lead_list', methods=['POST'])
@login_required
def delete_lead_list():
    id_del = int(request.form["id"])  # แปลงให้ชัวร์ว่าเป็น int
    print(f"Delete lead_id from LeadProgram: {id_del}")

    # ตรวจสอบว่า query เจอ
    target = db.session.query(LeadProgram).filter(LeadProgram.id == id_del).all()
    print("Target LeadPrograms:", target)

    if target:
        # ใช้ bulk delete
        db.session.query(LeadProgram).filter(LeadProgram.id == id_del).delete(synchronize_session=False)
        db.session.commit()
        flash('Deleted Program!', 'success')
    else:
        flash('No Program found for that lead', 'warning')

    return redirect(url_for('lead_blueprint.lead_list'))

@blueprint.route('/delete_follow_list', methods=['POST'])
@login_required
def delete_follow_list():
    id_del = int(request.form["id"])  # แปลงให้ชัวร์ว่าเป็น int
    print(f"Delete lead_id from LeadProgram: {id_del}")

    # ตรวจสอบว่า query เจอ
    target = db.session.query(LeadProgram).filter(LeadProgram.id == id_del).all()
    print("Target LeadPrograms:", target)

    if target:
        # ใช้ bulk delete
        db.session.query(LeadProgram).filter(LeadProgram.id == id_del).delete(synchronize_session=False)
        db.session.commit()
        flash('Deleted LeadProgram!', 'success')
    else:
        flash('No LeadProgram found for that lead_id.', 'warning')

    return redirect(url_for('lead_blueprint.follow_lead'))

@blueprint.route('/create_register_lead', methods=['POST'])
def create_register_lead():

    
    data = request.form
    print("data:",data)
    # username = data.get('username')
    # password = data.get('password')
    # confirm_password = data.get('confirm_password')

    # if not password or not confirm_password:
    #     print("⚠️ กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน")
    #     return jsonify({'status': 'error', 'message': 'กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน'}), 400

    # if password != confirm_password:
    #     print("⚠️ รหัสผ่านไม่ตรงกัน")
    #     return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    # if UserModel.query.filter_by(username=username).first():
    #     print("⚠️ Username นี้ถูกใช้งานแล้ว:", username)
    #     return jsonify({'status': 'error', 'message': 'Username นี้ถูกใช้งานแล้ว', "data": username }), 400

    # แฮชรหัสผ่าน
    # hashed_password = hash_pass(password)

    # role = RoleModel.query.filter(RoleModel.name == 'agency').first()
    # if not role:
    #     try:
    #         role = RoleModel(name='agency', description='Agency role')
    #         db.session.add(role)
    #         db.session.commit()
    #     except Exception as e:
    #         db.session.rollback()
    #         return jsonify({'success': False, 'message': 'Cannot create role', 'error': str(e)}), 400
    
    # # สร้าง User
    # user = UserModel(username=username, password=password, role_id=role.id)
    # db.session.add(user)
    # db.session.commit()
    # birth_date_raw = data.get('birth_date')

    # if birth_date_raw:
    #     try:
    #         birth_date_str = birth_date_raw.replace('/', '-')
    #         birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y")
    #     except ValueError:
    #         birth_date = None
    # else:
    #     birth_date = None

    # เตรียมข้อมูล
    agency_id = data.get('agency')
    agency_id = int(agency_id) if agency_id not in [None, '', 'None'] else None

   

    email = data.get('email')
    tel = data.get('phone')
    product_ids = data.getlist('project[]') or []
    if not product_ids:
        product_ids = []
    elif isinstance(product_ids, str):
        product_ids = [product_ids]
    # product = ProductForSalesModel.query.filter_by(id=product_ids).first()

    first_name = data.get('fullname')
    last_name = data.get('lastname')
    first_nameEN = data.get('firstnameEN')
    last_nameEN = data.get('lastnameEN')
    year = data.get('inputYear')
    gender = data.get('gender')
    line_id = data.get('line_id')
    nick_name = data.get('nickname')
    category_id = data.get('category')
    country_id = data.getlist('country[]') or []
    social = data.get('social')
    remask = data.get('remask')
    address = data.get('address')

    # เช็คว่า lead มีอยู่หรือยัง
    lead = leadModel.query.filter(
        or_(
            leadModel.email == email,
            leadModel.tel == tel
        )
    ).first()

    if not lead:
        lead = leadModel(
            first_name=first_name,
            last_name=last_name,
            first_nameEN=first_nameEN,
            last_nameEN=last_nameEN,
            year=year,
            tel=tel,
            email=email,
            status='new',
            gender=gender,
            line_id=line_id,
            nick_name=nick_name,
            category_id=category_id,
            # country_id=country_id,
            agency_id=agency_id,
            # product_id=product_id,
            social=social,
            remask=remask,
            address=address,
        )
        db.session.add(lead)
        db.session.flush()  # ให้ DB สร้าง lead.id ก่อน
    else:
        # อัปเดตข้อมูล lead เดิม
        lead.first_name = first_name
        lead.last_name = last_name
        lead.first_nameEN=first_nameEN
        lead.last_nameEN=last_nameEN
        lead.year = year    
        lead.first_name = first_name
        lead.last_name = last_name
        lead.nick_name = nick_name
        lead.tel = tel
        lead.email = email
        lead.gender = gender
        lead.line_id = line_id
        lead.agency_id = agency_id
        lead.category_id = category_id
        # lead.country_id = country_id
        # lead.product_id = product_id
        lead.social = social
        lead.remask = remask
        lead.address = address

    db.session.commit()

   
    # LeadProgram.query.filter_by(lead_id=lead.id).delete()
    # print("product_ids")
    # print(product_ids)
    # สร้าง LeadProgram ใหม่สำหรับทุกโปรเจคที่เลือก
    for pid in product_ids:
        try:
            pid = int(pid)
            product = ProductForSalesModel.query.filter_by(id=pid).first()
            if not product:
                print(f"[Warning] ไม่พบ product_id: {pid}")
                continue

            lead_program = LeadProgram(
                lead_id=lead.id,
                product_id=product.id,
                year=year,
                agency_id=agency_id,
                status='new',
                remask=remask
            )
            db.session.add(lead_program)

        except ValueError:
            print(f"[Error] product_id ไม่ถูกต้อง: {pid}")
            continue

    db.session.commit()

    # เก็บ session
    # session['waiting_user_id'] = lead.id
    # session['waiting_user_type'] = 'user'

    return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201


