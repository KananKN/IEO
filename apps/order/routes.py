
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
from sqlalchemy import and_, func, case, asc, or_, cast, String, desc,text
from sqlalchemy.orm import aliased, joinedload
from collections import defaultdict
from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP


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

def to_datetime(dt):
    if isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time())
    return None

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

# ดึงสถานะภาษาไทย
def get_status_label(status):
    if status and status.startswith("installment_"):
        seq = status.split("_")[1]
        return f"ค้างชำระเงินงวดที่ {seq}"
    if status == "completed":
        return "จบโครงการ"
    if status == "pending":
        return "รอการชำระเงิน"
    if status == "cancelled":
        return "ยกเลิก"
    return "สถานะไม่ทราบแน่ชัด"

status_label_expr = case(
    [
        (OrderModel.status.like("installment_%"),
         func.concat("ค้างชำระเงินงวดที่ ", func.split_part(OrderModel.status, "_", 2))),
        (OrderModel.status == "completed", "จบโครงการ"),
        (OrderModel.status == "pending", "รอการชำระเงิน"),
        (OrderModel.status == "cancelled", "ยกเลิก"),
    ],
    else_="สถานะไม่ทราบแน่ชัด"
)


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

    # ✅ Base query with joins for filtering and eager loading
    base_query = db.session.query(OrderModel)\
        .join(leadModel, OrderModel.lead_id == leadModel.id)\
        .join(ProductForSalesModel, OrderModel.product_id == ProductForSalesModel.id)\
        .options(
            joinedload(OrderModel.lead),
            joinedload(OrderModel.product).joinedload(ProductForSalesModel.term_of_payment),
            joinedload(OrderModel.product).joinedload(ProductForSalesModel.installments)
        )

    # 🔐 กรอง agency ถ้าไม่ใช่ admin
    role = RoleModel.query.get(current_user.role_id)
    # if role and role.name.lower() != 'admin':
    if role and role.name.lower() not in ['admin', 'STAFF']:
        if current_user.agency:
            base_query = base_query.filter(OrderModel.agency_id == current_user.agency.id)
        else:
            return Response(json.dumps({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": []
            }), content_type="application/json")
        
        
    # ✅ Count all records (before search)
    total_records = base_query.count()

    # ✅ Apply search filter (ถ้ามี)
    if search_value:
        search = f"%{search_value}%"
        base_query = base_query.filter(
            or_(
                OrderModel.order_number.ilike(search),
                leadModel.first_name.ilike(search),
                ProductForSalesModel.name.ilike(search),
                func.to_char(OrderModel.net_price, 'FM999999999.00').ilike(search),
                func.to_char(OrderModel.created_at, 'DD/MM/YYYY').ilike(search),
                status_label_expr.ilike(search),  # ✅ เพิ่มตรงนี้
            )
        )

    # ✅ Count records after filter
    filtered_records = base_query.count()

    # ✅ Sorting
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

    # ✅ Pagination
    orders = base_query.order_by(column_order).offset(start).limit(length).all()

    # ✅ Format response data
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
            "price": order.net_price,
            "created_at": int(order.created_at.timestamp() * 1000),
            "data_user": safe_model_to_dict(order),
            "lead": safe_model_to_dict(order.lead),
            "product": safe_model_to_dict(order.product),
            "agency_name": agency_name,
            "installments": installment_list,
            "status": order.status,
            "status_label": get_status_label(order.status),
        })

    # ✅ ส่งผลลัพธ์กลับ
    return Response(
        json.dumps({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
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
    
    print("orderTerm", orderTerm)
    # ✅ ถ้าไม่มีงวดผ่อนเลย
    if not orderTerm:
        for i, plan in enumerate(payment, start=1):
                term = OrderTermModel(
                    order_id=id,
                    term_detail=plan.term_detail,
                    amount=Decimal(plan.amount),
                    sequence=i,
                    discount=0.00,
                    net_price=Decimal(plan.amount),
                    outstanding_amount=Decimal(plan.amount),
                    check_vat=plan.check_vat
                )
                db.session.add(term)
        db.session.commit()
        print("✅ เพิ่ม OrderTerm สำเร็จ")
    
    # ✅ โหลดข้อมูลใหม่ เพื่อส่งไป render template
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
    
    receipts = ReceiptModel.query.filter_by(order_id=data.id).all()
    tax = TaxInvoiceModel.query.filter_by(order_id=data.id).all()

    for term in orderTerm:
        print(term.id, term.check_vat, type(term.check_vat))

    for t in tax:
        print(t.id, t.terms_id)  


    
    
    return render_template('order/order_update.html', segment='order' ,lead=lead, orderItem=orderItem, datas=data, payments=payments,product=product,members=member,orderTerms=orderTerm,term_payment_files_map=term_payment_files_map,
                           receipts=receipts,tax=tax)

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
    item_order = None
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
            item_member.nick_name = nickname
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

    # ✅ redirect อย่างปลอดภัย
    if item_order:
        return redirect(url_for('order_blueprint.order_update', id=id_order))
    else:
        return redirect(url_for('order_blueprint.order_update', id=id_order))

        # //return redirect(url_for('order_blueprint.get_order'))  # หรือหน้า fallback

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

        print(f"related_payment_ids: {related_payment_ids}")  

        paid_total = db.session.query(db.func.sum(PaymentModel.amount))\
                    .join(FilePaymentModel, PaymentModel.id == FilePaymentModel.payment_id)\
                    .filter(FilePaymentModel.term_id == term.id)\
                    .scalar() or 0

        print(f"paid_total: {paid_total}") 

        # paid_total = db.session.query(db.func.sum(PaymentModel.amount))\
        #     .filter(PaymentModel.id.in_(related_payment_ids)).scalar() or 0

        term.outstanding_amount = max(0, float(term.net_price or 0) - paid_total)
        db.session.commit()

        if term.outstanding_amount > 0:
            receipt_to_delete = ReceiptModel.query.filter_by(terms_id=term.id).all()
            with db.session.no_autoflush:
                for r in receipt_to_delete:
                    db.session.delete(r)
            db.session.commit()




        # ✅ ตรวจสอบสถานะ order ใหม่
        all_terms = OrderTermModel.query.filter_by(order_id=term.order_id).order_by(OrderTermModel.sequence).all()
        order_status = db.session.query(OrderModel).filter(OrderModel.id == term.order_id).first()


        # completed = True
        # for t in all_terms:
        #     if t.outstanding_amount and float(t.outstanding_amount) > 0.01:
        #         completed = False
        #         term.order.status = f"installment_{t.sequence}"
        #         order_status.status = f"installment_{t.sequence}"
        #         break

        any_payment = db.session.query(PaymentModel)\
        .join(FilePaymentModel, PaymentModel.id == FilePaymentModel.payment_id)\
        .join(OrderTermModel, FilePaymentModel.term_id == OrderTermModel.id)\
        .filter(OrderTermModel.order_id == term.order_id)\
        .count()

        if any_payment == 0:
            term.order.status = "pending"
            order_status.status = "pending"
            print("📭 ไม่มี payment ใดหลงเหลือ → เปลี่ยนสถานะเป็น pending")

        else:
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
                print("✅ ชำระครบ → สถานะเป็น completed")

 
        db.session.commit()

        print(f"🗑️ ลบไฟล์ของ term {term.sequence} → ยอดที่จ่ายเหลือ: {paid_total:.2f}, ค้าง: {term.outstanding_amount:.2f}")
        print(f"📦 อัปเดตสถานะ order: {term.order.status}")

    return redirect(url_for('order_blueprint.order_update', id=id_order))

@blueprint.route('/delete_order_list', methods=['POST'])
@login_required
def delete_order_list():
    id_del = int(request.form["id"])
    print("🧾 ลบออเดอร์ ID:", id_del)

    try:
        target = OrderModel.query.get(id_del)
        if not target:
            flash('ไม่พบข้อมูลออเดอร์', 'warning')
            return redirect(url_for('order_blueprint.order_list'))

        order_terms = OrderTermModel.query.filter_by(order_id=id_del).all()

        for term in order_terms:
            receipts = ReceiptModel.query.filter_by(terms_id=term.id).all()
            for r in receipts:
                db.session.delete(r)

        file_payments = FilePaymentModel.query.filter_by(order_id=id_del).all()
        for fp in file_payments:
            try:
                if fp.filename:
                    path = os.path.join("apps", "static", "assets", "files", "payment", fp.filename)
                    print("📂 Delete file:", path)
                    os.remove(path)
            except FileNotFoundError:
                print(f"⚠️ ไม่พบไฟล์: {path}")
            except Exception as e:
                print(f"❌ Error deleting file: {e}")

            db.session.delete(fp)

            if fp.payment_id:
                payment = PaymentModel.query.get(fp.payment_id)
                if payment and FilePaymentModel.query.filter_by(payment_id=payment.id).count() <= 1:
                    db.session.delete(payment)

        for term in order_terms:
            db.session.delete(term)

        db.session.delete(target)

        db.session.commit()
        flash('ลบออเดอร์และข้อมูลที่เกี่ยวข้องเรียบร้อย', 'success')
    except Exception as e:
        db.session.rollback()
        print("❌ Commit Error:", e)
        flash('เกิดข้อผิดพลาดระหว่างลบข้อมูล', 'danger')

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

    if term.outstanding_amount == 0:
        order = OrderModel.query.get(term.order_id)

        # ตรวจสอบว่าเคยมีใบเสร็จหรือยัง
        existing_receipt = ReceiptModel.query.filter_by(terms_id=term.id).first()
        if not existing_receipt:
            create_receipt_and_invoice_for_term(term,transfer_date=newItem.payment_date)
        else:
            print(f"📄 มีใบเสร็จแล้ว: {existing_receipt.receipt_no}")
            # create_receipt_and_invoice_for_term(term)
       
    

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
    print(f"\u2705 อัปเดตสถานะออร์เดอร์: {term.order.status}")

    try:
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=f"เกิดข้อผิดพลาด: {str(e)}")
    
def generate_document_number(doc_type="DP"):  # doc_type: "DP" หรือ "BI"
    # สมมุติใช้จาก ReceiptModel เป็นหลัก
    latest_receipt = db.session.query(ReceiptModel.receipt_no)\
        .filter(ReceiptModel.receipt_no.like(f"{doc_type}%"))\
        .order_by(ReceiptModel.receipt_no.desc()).first()

    if latest_receipt and latest_receipt[0]:
        # ดึงเฉพาะเลขรันสุดท้าย
        last_number = int(latest_receipt[0].split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    # ใช้ prefix แบบมีปีเดือนเพื่อให้ดูเวลาออกเอกสารได้ง่าย (แต่ไม่ส่งผลต่อเลขรัน)
    year_month = datetime.today().strftime("%Y%m")
    prefix = f"{doc_type}{year_month}"
    return prefix, str(next_number).zfill(5)

def generate_receipt_number():
    prefix, number = generate_document_number("DP")
    return f"{prefix}-{number}" 

def generate_tax_invoice_number():
    prefix, number = generate_document_number("BI")
    return f"{prefix}-{number}" 
     

def create_receipt_and_invoice_for_term(term: OrderTermModel, transfer_date=None):
    try:
        # เช็คก่อนว่า term นี้เคยออกใบเสร็จหรือยัง

        existing_receipt = ReceiptModel.query.filter_by(terms_id=term.id).first()
        print(f"[DEBUG] 🔢 Term ID: {term.id}, Sequence: {term.sequence}, Amount: {term.amount}, VAT: {term.check_vat}")
        if existing_receipt:
            print(f"⚠️ Term {term.id} มีใบเสร็จแล้ว: {existing_receipt.receipt_no}")
            return

        used_transfer_date = transfer_date or term.updated_at or term.created_at

            # สร้างใบเสร็จสำหรับงวดนี้
        receipt = ReceiptModel(
            order_id=term.order_id,
            terms_id=term.id,
            receipt_no=generate_receipt_number(),
            amount=term.amount,
            member_id=term.order.member_id,
            transfer_date=used_transfer_date
        )
        db.session.add(receipt)
        db.session.flush()
        

        
        # ตรวจสอบ VAT
        if term.check_vat:
            vat_rate = Decimal("1.07")
            amount = term.net_price  # สมมุติว่าเป็น Decimal อยู่แล้ว

            base_amount = (amount / vat_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            vat_amount = (amount - base_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            print(base_amount)
            print(vat_amount)
            tax_invoice = TaxInvoiceModel(
                order_id=term.order_id,
                receipt_id=receipt.id,
                tax_invoice_no=receipt.receipt_no.replace("DP", "BI"),
                member_id=term.order.member_id,
                amount=term.outstanding_amount,
                vat=vat_amount,  
                amount_before_vat=base_amount,
                terms_id=term.id,
                transfer_date=used_transfer_date
            )
            db.session.add(tax_invoice)
            db.session.commit()
            print(f"✅ งวด {term.sequence}: สร้างใบเสร็จ {receipt.receipt_no} และใบกำกับ {tax_invoice.tax_invoice_no}")
        else:
            db.session.commit()
            print(f"✅ งวด {term.sequence}: สร้างใบเสร็จ {receipt.receipt_no} (ไม่มี VAT)")

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR create_receipt_and_invoice_for_term: {e}")

@blueprint.route('/account')
@login_required
@read_permission.require(http_exception=403)
def account_list():
    datas = ReceiptModel.query.all()

    # ดึงข้อมูล tax invoice + terms + order + agency
    receipt = ReceiptModel.query \
        .options(
            joinedload(ReceiptModel.terms)
                .joinedload(OrderTermModel.order)
                .joinedload(OrderModel.agency),
            joinedload(ReceiptModel.member)
        ).all()

    # เอาเฉพาะ term ที่มีใบกำกับภาษี
    orderTerms = [inv.terms for inv in receipt if inv.terms]

    return render_template('order/account_list.html', 
                           segment='account',
                           receipts=receipt,  # <== ใบกำกับภาษีทั้งหมด
                           orderTerms=orderTerms)


    

@blueprint.route("/get_account", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_account():

    request_data = request.get_json()
    print("📥 Received JSON:", request_data) 
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])  # ✅ เพิ่มบรรทัดนี้
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: ReceiptModel.id,
        1: ReceiptModel.receipt_no,
        2: MemberModel.first_name,
        3: ProductForSalesModel.name,
        4: OrderTermModel.discount,       # ส่วนลดอยู่ที่ terms
        5: ReceiptModel.amount,
        6: ReceiptModel.created_at,
    }


    query = db.session.query(ReceiptModel,PaymentModel) \
    .join(ReceiptModel.member) \
    .join(ReceiptModel.terms) \
    .join(OrderTermModel.order) \
    .join(OrderModel.product) \
    .options(
        joinedload(ReceiptModel.member),
        joinedload(ReceiptModel.terms).joinedload(OrderTermModel.order).joinedload(OrderModel.product)
    ).outerjoin(
        PaymentModel, PaymentModel.order_id == OrderModel.id
    )



    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                ReceiptModel.receipt_no.ilike(search),
                MemberModel.first_name.ilike(search),
                MemberModel.last_name.ilike(search),
                ProductForSalesModel.name.ilike(search),
                func.to_char(ReceiptModel.created_at, 'DD/MM/YYYY').ilike(search),
                func.to_char(OrderTermModel.discount, 'FM999999999.00').ilike(search),
                func.to_char(OrderTermModel.amount, 'FM999999999.00').ilike(search),
                func.to_char(PaymentModel.payment_date, 'DD/MM/YYYY HH24:MI:SS').ilike(search),
            )
        )

    product_id = request_data.get("product_id")  # ✅ รับค่ามาจาก select

    print("Received product_id:", product_id)
        
    if product_id:
        query = query.filter(OrderModel.product_id == product_id)

    # ... (รับ product_id ไปแล้ว)
    start_datetime = request_data.get("start_datetime")
    end_datetime = request_data.get("end_datetime")

    print("✅ start_datetime:", start_datetime)
    print("✅ end_datetime:", end_datetime)
    if start_datetime and end_datetime:
        try:
            start_dt = datetime.strptime(start_datetime, "%d-%m-%Y %H:%M:%S")
            end_dt = datetime.strptime(end_datetime, "%d-%m-%Y %H:%M:%S")

            # filter เฉพาะรายการที่อยู่ในช่วงเวลา
            query = query.filter(PaymentModel.payment_date != None)
            query = query.filter(PaymentModel.payment_date.between(start_dt, end_dt))
        except ValueError:
            print("❌ Invalid datetime format")

    print("Count:", query.count())
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
    for index, (order, payment) in enumerate(orders):
        member = order.member
        term = order.terms
        order_model = term.order if term else None
        product = order_model.product if order_model else None

        customer_name = f"{member.first_name or ''} {member.last_name or ''}".strip() if member else ''
        product_name = product.name if product else ''
        discount = term.discount if term else 0

        payment_date = to_datetime(payment.payment_date) if payment and payment.payment_date else None

        data.append({
            "id": start + index + 1,
            "term_id": order.terms_id,
            "receipt_no": order.receipt_no or '',
            "customer_name": customer_name,
            "product_name": product_name,
            "discount": float(discount or 0),
            "amount": float(order.amount or 0),
            "created_at": int(payment_date.timestamp() * 1000) if payment_date else None,
            "data_user": safe_model_to_dict(order),
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

@blueprint.route('/invoice')
@login_required
@read_permission.require(http_exception=403)
def invoice_list():
    


    # ดึงข้อมูล tax invoice + terms + order + agency
    invoices = TaxInvoiceModel.query \
        .options(
            joinedload(TaxInvoiceModel.terms)
                .joinedload(OrderTermModel.order)
                .joinedload(OrderModel.agency),
            joinedload(TaxInvoiceModel.member)
        ).all()

    # เอาเฉพาะ term ที่มีใบกำกับภาษี
    orderTerms = [inv.terms for inv in invoices if inv.terms]

    return render_template('order/invoice_list.html', 
                           segment='invoice',
                           tax=invoices,  # <== ใบกำกับภาษีทั้งหมด
                           orderTerms=orderTerms)

@blueprint.route("/get_invoice", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_invoice():
    request_data = request.get_json()

    # ───── ข้อมูลพื้นฐานจาก DataTables ─────
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # ───── Mapping คอลัมน์จาก DataTable ไปยัง Model ─────
    column_map = {
        0: TaxInvoiceModel.id,
        1: TaxInvoiceModel.tax_invoice_no,
        2: MemberModel.first_name,
        3: ProductForSalesModel.name,
        4: OrderTermModel.discount,
        5: TaxInvoiceModel.amount,
        6: TaxInvoiceModel.created_at,
    }

    # ───── Query หลัก ─────
    query = db.session.query(TaxInvoiceModel,PaymentModel)\
        .join(TaxInvoiceModel.member)\
        .join(TaxInvoiceModel.terms)\
        .join(OrderTermModel.order)\
        .join(OrderModel.product)\
        .options(
            joinedload(TaxInvoiceModel.member),
            joinedload(TaxInvoiceModel.terms)
                .joinedload(OrderTermModel.order)
                .joinedload(OrderModel.product)
        ).outerjoin(
        PaymentModel, PaymentModel.order_id == OrderModel.id
    )

    # ───── ค้นหาจากคำค้น (Search) ─────
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                TaxInvoiceModel.tax_invoice_no.ilike(search),
                MemberModel.first_name.ilike(search),
                MemberModel.last_name.ilike(search),
                ProductForSalesModel.name.ilike(search),
                func.to_char(TaxInvoiceModel.created_at, 'DD/MM/YYYY').ilike(search),
                func.to_char(TaxInvoiceModel.vat, 'FM999999999.00').ilike(search),
                func.to_char(TaxInvoiceModel.amount_before_vat, 'FM999999999.00').ilike(search),
                func.to_char(OrderTermModel.amount, 'FM999999999.00').ilike(search),
                func.to_char(OrderTermModel.net_price, 'FM999999999.00').ilike(search),
                func.to_char(PaymentModel.payment_date, 'DD/MM/YYYY HH24:MI:SS').ilike(search),
            )
        )
    
    product_id = request_data.get("product_id")  # ✅ รับค่ามาจาก select

    print("Received product_id:", product_id)
        
    if product_id:
        query = query.filter(OrderModel.product_id == product_id)
    
    # ... (รับ product_id ไปแล้ว)
    start_datetime = request_data.get("start_datetime")
    end_datetime = request_data.get("end_datetime")

    print("✅ start_datetime:", start_datetime)
    print("✅ end_datetime:", end_datetime)
    if start_datetime and end_datetime:
        try:
            start_dt = datetime.strptime(start_datetime, "%d-%m-%Y %H:%M:%S")
            end_dt = datetime.strptime(end_datetime, "%d-%m-%Y %H:%M:%S")

            # filter เฉพาะรายการที่อยู่ในช่วงเวลา
            query = query.filter(PaymentModel.payment_date != None)
            query = query.filter(PaymentModel.payment_date.between(start_dt, end_dt))
        except ValueError:
            print("❌ Invalid datetime format")

    # ───── จัดเรียงข้อมูล (Ordering) ─────
    if order:
        column_index = int(order[0]["column"])
        sort_direction = order[0]["dir"]
        column_order = column_map.get(column_index, TaxInvoiceModel.id)  # fallback
        column_order = column_order.desc() if sort_direction == "desc" else column_order.asc()
    else:
        column_order = TaxInvoiceModel.id.asc()

    total_records = query.count()

    # ───── ดึงข้อมูลรายการตามช่วงที่ต้องการ ─────
    invoices = query.order_by(column_order).offset(start).limit(length).all()

    # ───── เตรียมข้อมูลสำหรับ DataTables ─────
    data = []
    for index, (invoice, payment) in enumerate(invoices):
        member = invoice.member
        term = invoice.terms
        order_model = term.order if term else None
        product = order_model.product if order_model else None

        customer_name = f"{member.first_name or ''} {member.last_name or ''}".strip() if member else ''
        product_name = product.name if product else ''
        discount = float(term.discount or 0) if term else 0
        amount = float(term.amount or 0) if term else 0
        net_price = float(term.net_price or 0) if term else 0
        vat = float(invoice.vat or 0) if invoice else 0
        amount_before_vat = float(invoice.amount_before_vat or 0) if invoice else 0
        payment_date = to_datetime(payment.payment_date) if payment and payment.payment_date else None


        data.append({
            "id": start + index + 1,
            "term_id": invoice.terms_id,
            "tax_invoice_no": invoice.tax_invoice_no or '',
            "customer_name": customer_name,
            "product_name": product_name,
            "discount": discount,
            "amount": amount,
            "net_price": net_price,
            "vat": vat,
            "amount_before_vat": amount_before_vat,
            "created_at": int(payment_date.timestamp() * 1000) if payment_date else None,
            "data_user": safe_model_to_dict(invoice),
        })

    # ───── ส่งผลลัพธ์กลับ DataTables ─────
    return Response(
        json.dumps({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data
        }, ensure_ascii=False, default=str),
        content_type="application/json"
    )

@blueprint.route("/get_product_list")
def get_product_list():
    products = ProductForSalesModel.query.all()
    result = [{"id": p.id, "name": p.name} for p in products]
    return jsonify(result)
    