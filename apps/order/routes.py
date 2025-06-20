
import time
import re
from apps.order import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.order.models import *
from apps.lead.models import *

from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, Response,current_app, abort
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
from sqlalchemy.orm import aliased, joinedload
from collections import defaultdict
from datetime import datetime

# import logging

# logging.basicConfig(filename='error.log', level=logging.ERROR)

read_permission = Permission(RoleNeed("read_order"))
write_permission = Permission(RoleNeed("write_order"))
delete_permission = Permission(RoleNeed("delete_order"))

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
        print(dt)
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
def convert_status_text(status):
    if status and status.startswith("installment_"):
        try:
            n = status.split("_")[1]
            return f"ชำระเงินงวดที่ {n}"
        except:
            return "สถานะไม่ถูกต้อง"
    elif status == "completed":
        return "จบโครงการ"
    elif status == "cancelled":
        return "ยกเลิก"
    else:
        return "สถานะไม่ทราบแน่ชัด"

def parse_decimal(val):
    return Decimal(val.replace(',', '')) if val else Decimal('0.00')
    
@blueprint.app_template_filter("comma")
def comma_filter(value):
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return value

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
# -----------------------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def order_list():
    datas = OrderModel.query.all()

    memvber = MemberModel.query.all()
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
    return render_template('order/order_list.html', segment='order' ,datas=datas,categorys=category,countrys=country, agencys=agencies_with_IEO,product=product,social_channels=social_channels )


def convert_thai_to_date(thai_date_str):
    # แปลง พ.ศ. เป็น ค.ศ.
    day, month, year_th = thai_date_str.split("/")
    year = int(year_th) - 543  # เปลี่ยนจาก พ.ศ. เป็น ค.ศ.
    
    # สร้างเป็นวันที่ในรูปแบบ datetime
    return datetime(year, int(month), int(day))

@blueprint.route("/get_order1", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_order():

    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: OrderModel.id,
        1: OrderModel.order_number,
        2: leadModel.first_name,  # ปรับชื่อให้ตรงกับ model
        3: ProductForSalesModel.name,
        4: ProductForSalesModel.price,
        6: OrderModel.created_at,
    }

    query = db.session.query(OrderModel) \
    .options(
        joinedload(OrderModel.lead),
        joinedload(OrderModel.product).joinedload(ProductForSalesModel.term_of_payment),
        joinedload(OrderModel.product).joinedload(ProductForSalesModel.installments)
    )

    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                OrderModel.order_number.ilike(search),
                leadModel.first_name.ilike(search),
                ProductForSalesModel.name.ilike(search),
                ProductForSalesModel.price.ilike(search),
                func.to_char(OrderModel.created_at, 'DD-MM-YYYY').ilike(search),
                OrderModel.status.ilike(search),
            )
        )

    # การจัดเรียง
    if order:
        column_index = int(order[0]["column"])
        sort_direction = order[0]["dir"]
        column_order = column_map.get(column_index, OrderModel.id)

        if sort_direction == "desc":
            column_order = column_order.desc()
        else:
            column_order = column_order.asc()
    else:
        column_order = OrderModel.id.asc()

    total_records = query.count()

    orders = query.order_by(column_order).offset(start).limit(length).all()
    # print(orders)
    data = []
    for index, order in enumerate(orders):
        customer_name = f"{order.lead.first_name or ''} {order.lead.last_name or ''}".strip() if order.lead else ''

        agency_name = (
            "IEO" if not order.lead or not order.lead.agency
            else f"{order.lead.agency.first_name or ''} {order.lead.agency.last_name or ''}".strip()
        )

        installment_list = [safe_model_to_dict(i) for i in order.product.installments] if order.product and order.product.installments else []

        data.append({
            "id": start + index + 1, 
            "order_number": order.order_number or '',
            "customer_name": customer_name,
            "product_name": order.product.name if order.product else '',
            "term": order.product.term_of_payment.name if order.product and order.product.term_of_payment else '',
            "email": order.lead.email if order.lead else '',
            "price": order.net_price ,
            "created_at": int(order.created_at.timestamp() * 1000),
            "data_user": safe_model_to_dict(order),
            "lead": safe_model_to_dict(order.lead),
            "product": safe_model_to_dict(order.product),
            "agency_name": agency_name,
            "installments": installment_list,
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

@blueprint.route('/order_create')
@login_required
@read_permission.require(http_exception=403)
def order_create():
    datas = MemberModel.query.all()
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
    return render_template('order/order_create.html', segment='order' ,datas=datas, )

@blueprint.route('/order_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def order_update(id):
    data = OrderModel.query.filter_by(id=id).first()
    if not data:
        abort(404, description="ไม่พบข้อมูล Lead ที่คุณต้องการ")

    lead = leadModel.query.filter_by(id=data.lead_id).first()
    
    orderItem = OrderItemModel.query.filter_by(product_id=data.product_id).first()
    product = ProductForSalesModel.query.filter_by(id=data.product_id).first()
    member = MemberModel.query.filter_by(id=data.member_id).first()
    # payment = installmentsPaymentModel.query.filter_by(product_for_sales_id=product.id).all()
    payment = installmentsPaymentModel.query.filter(
                    installmentsPaymentModel.product_for_sales_id == product.id,
                    installmentsPaymentModel.year == str(product.year)
                ).all()
    
    orderTerm = OrderTermModel.query.filter(
                    OrderTermModel.order_id == data.id,
                ).order_by(OrderTermModel.sequence).all()
    
    # 1. ดึงข้อมูล payments
    payments = PaymentModel.query.filter_by(order_id=data.id).all()

    # 2. สร้าง dict mapping payment_id -> payment object
    payment_map = {p.id: p for p in payments}

    # 3. ดึงข้อมูลไฟล์ที่ term_id มีค่า (เพื่อเชื่อมกับงวด)
    file_data = FilePaymentModel.query.filter(
        FilePaymentModel.order_id == data.id,
        FilePaymentModel.term_id.isnot(None)
    ).all()

    # 4. สร้าง dict term_id -> [ {file, payment} ]
    term_payment_files_map = {}
    for file in file_data:
        related_payment = payment_map.get(file.payment_id)

        if file.term_id not in term_payment_files_map:
            term_payment_files_map[file.term_id] = []

        term_payment_files_map[file.term_id].append({
            "file": file,
            "payment": related_payment
        })
    
    print("term_payment_files_map")
    print(term_payment_files_map)
    
    
    return render_template('order/order_update.html', segment='order' ,lead=lead, orderItem=orderItem, datas=data, payments=payments,product=product,members=member,orderTerms=orderTerm,term_payment_files_map=term_payment_files_map)

@blueprint.route("/check_statusLead", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def check_statusLead():
    json_data = request.get_json()

    id =json_data["id"]
    status =json_data["status"]
    remask =json_data["remask"]
    
    check_id = leadModel.query.filter_by(id=id).first()
    
    
    if not check_id:
        print("⚠️ ไม่พบข้อมูล:", check_id)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ไม่พบข้อมูล', "data": check_id}), 400

    else:
        thisItem = leadModel.query.filter_by(id=id).first()
        thisItem.status = status
        thisItem.remask = remask
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
    


@blueprint.route('/save_payment', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def save_payment():
    print("save_payment",request.form)

    # print(request.form.get('id'))
    try:
        id_order = request.form.get('id')
        id_member = request.form.get('id_member')
        first_name = request.form.get('first_name')
        first_nameEN = request.form.get('first_nameEN')
        last_name = request.form.get('last_name')
        last_nameEN = request.form.get('last_nameEN')
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        phone = request.form.get('phone')
        address = request.form.get('address')


        order_code = request.form.get('order_code')
        payment_no=request.form.get('cash_payment')
        # status =request.form.get('cash_payment')
        # amount =request.form.get('amount')
        # payment_date =request.form.getlist('payment_date')
        note =request.form.get('note')
        
        # raw_amount = request.form.get("amount", "0").replace(",", "")
        # amount = float(raw_amount) 

        raw_sum_discount = request.form.get("sum_discount", "0").replace(",", "")
        sum_discount = float(raw_sum_discount) 

        raw_sum_installments = request.form.get("sum_installments", "0").replace(",", "")
        sum_installments = float(raw_sum_installments) 
        
        raw_total_payment = request.form.get("total_payment", "0").replace(",", "")
        total_payment = float(raw_total_payment) 

        term_id = request.form.getlist('term_id')
        installments = request.form.getlist('installments')
        discounts = request.form.getlist('discount')
        counts = request.form.getlist('count')
        outstanding_amounts = request.form.getlist('outstanding_amount')
        
        
        item_order= OrderModel.query.filter_by(id=id_order).first()
        item_member = MemberModel.query.filter_by(id=item_order.member_id).first()
        if not item_order:
            flash("ไม่มีออร์เดอร์นี้: ", "warning")
            return redirect(url_for('order_blueprint.order'))
         
        # if name_check:
        #     flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        else :
            item_order.status = payment_no
            item_order.discount = sum_discount
            item_order.net_price = total_payment
            item_order.total_price = sum_installments
            item_order.note = note

            item_member.first_name = first_name
            item_member.first_nameEN = first_nameEN
            item_member.last_nameEN = last_nameEN
            item_member.last_name = last_name       
            item_member.email = email
            item_member.nickname = nickname
            item_member.phone = phone   
            item_member.address = address
            item_member.status = payment_no
            db.session.commit()

            print(f"Received term_id: {term_id}")
            print(f"Received discounts: {discounts}")
            print(f"Received counts: {counts}")
            # print(f"Received payment_dates: {payment_dates}")

            updated_order_id = None 
            for i in range(len(term_id)):
                current_term_id = int(term_id[i])
                discount = parse_decimal(discounts[i])
                net_price = parse_decimal(counts[i])
                outstanding_amount = parse_decimal(outstanding_amounts[i])
                
                term = OrderTermModel.query.get(current_term_id)
                print(f"Processing term_id={current_term_id}, discount={discount}, net_price={net_price}")
                print(f"Term found? {term is not None}")

                if term:
                    print(f"Term found? {term is not None}") 
                    term.discount = discount
                    term.net_price = net_price
                    term.outstanding_amount = outstanding_amount
                    # term.payment_date = payment_dt

                     # จำ order_id ไว้
                    if updated_order_id is None:
                        updated_order_id = term.order_id
                    
                else:
                    print(f"❌ ไม่พบ OrderTermModel id: {current_term_id}")
            db.session.commit()

            if updated_order_id:
                order = OrderModel.query.get(updated_order_id)
                if order:
                    all_terms = order.terms.order_by(OrderTermModel.sequence).all()

                    # ✅ หา term แรกที่ยังมียอดค้าง > 0.01
                    next_term = next((t for t in all_terms if float(t.outstanding_amount or 0) > 0.01), None)

                    if next_term:
                        order.status = f"installment_{next_term.sequence}"
                        print(f"📌 พบงวดที่ยังค้าง → ตั้งสถานะเป็น {order.status}")
                    else:
                        order.status = "completed"
                        print("✅ ชำระครบทุกงวด → ตั้งสถานะเป็น completed")  
                    db.session.commit()
            
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback() 

    return redirect(url_for('order_blueprint.order_update',id=item_order.id))

@blueprint.route('/downloadPayment/<filename>')
def downloadPayment(filename):

    file = FilePaymentModel.query.filter_by(filename=filename).first()
   
    if not file:
        abort(404, description="File record not found in database")

    # สร้าง path แบบ absolute ด้วย current_app.root_path
    file_path = os.path.join(current_app.root_path, "static", "assets", "files", "payment", file.filename)

    # เช็คว่ามีไฟล์อยู่จริงหรือไม่
    if not os.path.exists(file_path):
        abort(404, description="File not found on server")

    return send_file(file_path, as_attachment=True)


@blueprint.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    id_file = request.form["id_file"]
    id_order = request.form["id_order"]

    print(id_order)
    thisFile = FilePaymentModel.query.filter_by(id=id_file).first()
    thisPayment = PaymentModel.query.filter_by(order_id=id_order).first()

    # เก็บข้อมูลไว้ก่อนลบ
    term_id = thisFile.term_id
    payment_id = thisFile.payment_id

    try:
        path = os.path.join("apps", "static", "assets", "files", "payment", thisFile.filename)
        os.remove(path)
    except FileNotFoundError:
        print(f"ไม่พบไฟล์ในระบบไฟล์: {path}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")

    db.session.delete(thisFile)

    # ลบ payment ถ้าไม่มีไฟล์อื่นผูกอยู่
    if payment_id:
        remain_files = FilePaymentModel.query.filter_by(payment_id=payment_id).count()
        if remain_files == 0:
            thisPayment = PaymentModel.query.filter_by(id=payment_id).first()
            if thisPayment:
                db.session.delete(thisPayment)

    db.session.commit()

    # ✅ คำนวณยอดคงเหลือใหม่
    term = OrderTermModel.query.get(term_id)
    if term:
        related_files = FilePaymentModel.query.filter_by(term_id=term.id).all()
        related_payment_ids = [f.payment_id for f in related_files if f.payment_id]

        paid_total = db.session.query(db.func.sum(PaymentModel.amount))\
            .filter(PaymentModel.id.in_(related_payment_ids)).scalar() or 0

        term.outstanding_amount = max(0, float(term.amount or 0) - paid_total)
        db.session.commit()

        # ✅ ตรวจสอบสถานะ order ใหม่
        all_terms = OrderTermModel.query.filter_by(order_id=term.order_id).order_by(OrderTermModel.sequence).all()
        order_status = db.session.query(OrderModel).filter(OrderModel.id == term.order_id).first()


        completed = True
        for t in all_terms:
            if t.outstanding_amount and float(t.outstanding_amount) > 0.01:
                completed = False
                term.order.status = f"installment_{t.sequence}"
                order_status.status = f"installment_{t.sequence}"
                break

        if completed:
            term.order.status = "completed"
            order_status.status = "completed"
 
        db.session.commit()

        print(f"🗑️ ลบไฟล์ของ term {term.sequence} → ยอดที่จ่ายเหลือ: {paid_total:.2f}, ค้าง: {term.outstanding_amount:.2f}")
        print(f"📦 อัปเดตสถานะ order: {term.order.status}")

    return redirect(url_for('order_blueprint.order_update', id=id_order))

@blueprint.route('/delete_order_list', methods=['POST'])
@login_required
def delete_order_list():
    id_del = int(request.form["id"])  # แปลงให้ชัวร์ว่าเป็น int

    print(id_del)
    # ตรวจสอบว่า query เจอ
    target = db.session.query(OrderModel).filter(OrderModel.id == id_del).first()
    print("Target Order:", target)

    if target:
        # ลบ OrderTermModel ที่อ้างถึง order_id นี้ก่อน
        OrderTermModel.query.filter_by(order_id=id_del).delete()
        db.session.commit()

        # แล้วค่อยลบ OrderModel
        db.session.query(OrderModel).filter(OrderModel.id == id_del).delete(synchronize_session=False)
        db.session.commit()

        flash('Deleted Order!', 'success')
    else:
        flash('No Order found for that ID', 'warning')

    return redirect(url_for('order_blueprint.order_list'))

@blueprint.route("/create_order", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def create_order():
    json_data = request.get_json()
    print(json_data)
    
    product_id_value =json_data["product_id"]
    first_name =json_data["first_name"]
    last_name =json_data["last_name"]
    first_nameEN =json_data["first_nameEN"]
    last_nameEN =json_data["last_nameEN"]
    year =json_data["year"]
    nickname =json_data["nickname"]
    email =json_data["email"]
    tel =json_data["tel"]
    category_id =json_data["category_id"]
    country_id =json_data["country_id"]
    gender =json_data["gender"]
    line_id =json_data["line_id"]
    address =json_data["address"]

    agency_id = json_data.get("agency_id")
    if agency_id == 'None' or agency_id == '':
        agency_id = None

  
    lead = leadModel.query.filter(
            or_(
                leadModel.email == email,
                leadModel.tel == tel  # หรือจะเปลี่ยนชื่อเป็น `tel` ด้วยก็ได้
            )).first()
    product = ProductForSalesModel.query.filter_by(id=product_id_value).first()
    if not product:
        return jsonify({"status": "error", "message": "ไม่พบสินค้า"}), 404
    

    # return
    if not lead:
        thisItem = leadModel(
            first_name=first_name,
            last_name=last_name,
            first_nameEN=first_nameEN,
            last_nameEN=last_nameEN,
            nick_name=nickname,
            tel=tel,
            email=email,
            gender=gender,
            line_id=line_id,
            address=address,
            agency_id=agency_id,
            product_id=product.id,
            category_id=category_id,
            country_id=country_id,
        )
        db.session.add(thisItem)
        db.session.commit()

        lead = thisItem

    else:
        thisItem = leadModel.query.filter_by(id=lead.id).first()
        
        thisItem.first_name=first_name
        thisItem.last_name=last_name
        thisItem.first_nameEN=first_nameEN
        thisItem.last_nameEN=last_nameEN
        thisItem.year=year
        thisItem.nick_name=nickname
        thisItem.email=email
        thisItem.tel=tel
        thisItem.agency_id=agency_id
        thisItem.category_id=category_id
        thisItem.country_id=country_id
        thisItem.product_id=product.id
        thisItem.gender=gender
        thisItem.line_id=line_id
        thisItem.address=address


        
    thisProgram = LeadProgram.query.filter_by(
                    lead_id=int(thisItem.id),
                    product_id=int(thisItem.product_id)
                ).first()
    
    status = 'converted'

    existing_order = None
    current_year = datetime.utcnow().year
    # print("current_year", current_year)
    if status == 'converted':
        existing_order = db.session.query(OrderModel).filter(
                        OrderModel.lead_id == int(thisItem.id),
                        OrderModel.status.notin_(['completed', 'cancelled']),
                        # db.extract('year', OrderModel.created_at) == current_year
                    ).first()

    # === จัดการ LeadProgram ===
    if thisProgram:
        # แก้ไขข้อมูลเดิม
        thisProgram.product_id = product.id
        thisProgram.agency_id = agency_id
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
            year=year
        )
        db.session.add(new_program)

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
                existing_member.nick_name = lead.nick_name
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
                    nick_name=lead.nick_name,
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

            
            product_price = Decimal(str(product.price or 0))

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
                total_price=product_price,
                discount=0.00,
                net_price=product_price,
                
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
                    created_at=datetime.utcnow()
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

@blueprint.route('/save_single_term', methods=['POST'])
def save_single_term():
    term_id = request.form.get("term_ids")
    payment_date = request.form.get("payment_date")
    amount = request.form.get("amount")
    file = request.files.get("formFile_payment")
    total_pay = request.files.get("total_pay")

    raw_amount = request.form.get("amount", "0").replace(",", "")
    amount = float(raw_amount) 
    raw_total_pay = request.form.get("total_pay", "0").replace(",", "")
    total_pay = float(raw_total_pay) 

    

    # แปลงวันที่
    # payment_dt = None
    if payment_date:
        try:
            payment_date = datetime.strptime(payment_date.strip(), '%d-%m-%Y %H:%M')
        except Exception:
            return jsonify(success=False, error="รูปแบบวันที่ไม่ถูกต้อง (dd-mm-yyyy)")
    # return
    if not term_id:
        return jsonify(success=False, error="Missing term_id")

    term = OrderTermModel.query.get(term_id)
    if not term:
        return jsonify(success=False, error="ไม่พบงวดนี้ในระบบ")
    
        
    payment_no = f'installment_{term.sequence}'
    member = term.order.member_id
    order_id=term.order_id

    # check_payment = PaymentModel.query.filter_by(order_id=order_id).first()
    # if check_payment :
    #     check_payment.amount = amount
    #     check_payment.payment_date=payment_date
    #     # check_payment.note=note
    #     check_payment.status='pending',
    # else :
    newItem = PaymentModel(
        order_id=term.order_id,
        product_id=term.order.product_id,
        amount=amount,
        payment_date=payment_date,
        # note=note,
        payment_no=payment_no,
        status= 'pending',
        sequence=term.sequence
    )
    db.session.add(newItem)
    db.session.flush() 
   # ยังไม่ commit ตอนนี้

    # คำนวณยอดรวมโดยไม่รวม payment ใหม่ล่าสุด
    # (กรณีที่คุณต้องการดูยอดก่อนบันทึก)
    total_paid = db.session.query(db.func.sum(PaymentModel.amount))\
            .filter(
                PaymentModel.order_id == newItem.order_id,
                PaymentModel.product_id == newItem.product_id,
                PaymentModel.sequence == newItem.sequence,
                PaymentModel.id != newItem.id  # ✅ ไม่รวมตัวใหม่
            ).scalar() or 0

    # เพิ่มของใหม่เข้าไปเองถ้าต้องการ:
    total_paid += amount
    

    net_price = term.net_price or 0
    outstanding_amount = round(float(net_price) - total_paid, 2)

    print("net_price", net_price)
    print("total_paid", total_paid)
    print("outstanding_amount", outstanding_amount)

    # อัปเดตยอดใน term
    term.outstanding_amount = outstanding_amount

    db.session.commit()

    

    # บันทึกไฟล์
    file_PO = file
    if file_PO and file_PO.filename != '':
        target = 'apps/static/assets/files/payment/'
        os.makedirs(target, exist_ok=True)

        ftype = file_PO.filename.rsplit('.', 1)[-1]  # นามสกุลไฟล์
        filename = f'SLIP{term.order.order_number}_{payment_no}.{ftype}'
        file_path = os.path.join(target, filename)

        try:
            file_PO.save(file_path)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        newfile = FilePaymentModel(
            filename=filename,
            filepath=file_path,
            file_type=1,
            order_id=term.order_id,
            term_id=term_id,  # ต้องเพิ่ม field term_id ใน model ด้วย
            payment_date=payment_date,
            payment_id=newItem.id
        )
        db.session.add(newfile)
        db.session.commit()

        print(f"[INFO] บันทึกไฟล์: {filename} ที่ {file_path}")

    # คำนวณยอดคงเหลือของ term ปัจจุบัน
    # 1. หา term ทั้งหมดของ order
    order_id = term.order_id
 

    # ตรวจสอบสถานะของ order
    all_terms = OrderTermModel.query.filter_by(order_id=term.order_id).order_by(OrderTermModel.sequence).all()
    order = OrderModel.query.get(term.order_id)

    # ค้นหางวดแรกที่ยังค้าง
    next_outstanding_term = next((t for t in all_terms if float(t.outstanding_amount or 0) > 0.01), None)

    # อัปเดตสถานะ
    if next_outstanding_term:
        order.status = f"installment_{next_outstanding_term.sequence}"
    else:
        order.status = "completed"

    db.session.commit()

    # print(f"\u2705 บันทึกงวด {term.sequence} ยอดจ่ายรวม: {paid_total:.2f}, ค้าง: {term.outstanding_amount:.2f}")
    # print(f"\u2705 อัปเดตสถานะออร์เดอร์: {term.order.status}")

    try:
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=f"เกิดข้อผิดพลาด: {str(e)}")
    
    