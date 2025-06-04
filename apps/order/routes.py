
import time
import re
from apps.order import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.order.models import *
from apps.lead.models import *

from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, Response
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
    
# -----------------------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def order_list():
    datas = OrderModel.query.all()
    # print(datas)
    return render_template('order/order_list.html', segment='order' ,datas=datas, )


def convert_thai_to_date(thai_date_str):
    # แปลง พ.ศ. เป็น ค.ศ.
    day, month, year_th = thai_date_str.split("/")
    year = int(year_th) - 543  # เปลี่ยนจาก พ.ศ. เป็น ค.ศ.
    
    # สร้างเป็นวันที่ในรูปแบบ datetime
    return datetime(year, int(month), int(day))

@blueprint.route("/get_order", methods=["POST"])
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
            "price": order.price ,
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
    datas = leadModel.query.all()
    # print(datas)
    return render_template('order/order_create.html', segment='order_create' ,datas=datas, )

@blueprint.route('/order_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def order_update(id):
    data = OrderModel.query.filter_by(id=id).first()
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
    
    print("payment",payment)
    payment11 = PaymentModel.query.filter_by(order_id=data.id).all()

    file_data = FilePaymentModel.query.filter_by(order_id  = data.id).all()
    print("data",data)
    print("lead",lead)
    print("orderItem",orderItem )
    return render_template('order/order_update.html', segment='order' ,lead=lead, orderItem=orderItem, datas=data, payments=payment,product=product,members=member,file_datas=file_data,orderTerms=orderTerm)

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
        order_code = request.form.get('order_code')
        payment_no=request.form.get('cash_payment')
        # status =request.form.get('cash_payment')
        amount =request.form.get('amount')
        payment_date =request.form.get('payment_date')
        note =request.form.get('note')
        formFile_payment = request.form.get('formFile_payment')
        
        raw_amount = request.form.get("amount", "0").replace(",", "")
        amount = float(raw_amount) 

        raw_sum_discount = request.form.get("sum_discount", "0").replace(",", "")
        sum_discount = float(raw_sum_discount) 

        raw_sum_installments = request.form.get("sum_installments", "0").replace(",", "")
        sum_installments = float(raw_sum_installments) 
        
        raw_total_payment = request.form.get("total_payment", "0").replace(",", "")
        total_payment = float(raw_total_payment) 

        term_ids = request.form.getlist('term_id')
        installments = request.form.getlist('installments')
        discounts = request.form.getlist('discount')
        counts = request.form.getlist('count')
        
        
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
            item_member.status = payment_no
            db.session.commit()

            for i in range(len(term_ids)):
                
                term_id = int(term_ids[i])
                discount = parse_decimal(discounts[i])
                net_price = parse_decimal(counts[i])
                print(discount)
                print(net_price)
                # ค้นหา term ที่จะอัปเดต
                term = OrderTermModel.query.get(term_id)
                if term:
                    term.discount = discount
                    term.net_price = net_price
                else:
                    print(f"❌ ไม่พบ OrderTermModel id: {term_id}")
            db.session.commit()
            amount_raw = request.form.get("amount", "").replace(",", "").strip()

            # ตรวจสอบว่ามีค่า และไม่ใช่ 0
            if amount_raw != 0:
                try:
                    amount_float = float(amount_raw)
                    payment_date_str = request.form.get("payment_date") 
                    payment_date = datetime.strptime(payment_date_str, "%d-%m-%Y") 
                    if amount_float > 0:
                        check_payment = PaymentModel.query.filter_by(payment_no=payment_no).first()
                        if check_payment :
                            check_payment.amount = amount_float
                            check_payment.payment_date=payment_date
                            check_payment.note=note
                            check_payment.status='pending',
                        else :
                            newItem = PaymentModel(
                                order_id=id_order,
                                product_id=item_order.product_id,
                                amount=amount_float,
                                payment_date=payment_date,
                                note=note,
                                payment_no=payment_no,
                                status= 'pending',
                            )
                            db.session.add(newItem)
                        db.session.commit()
                    else:
                        print("[INFO] amount เป็น 0, ไม่บันทึกข้อมูล")
                except ValueError:
                    print(f"[ERROR] amount ไม่สามารถแปลงเป็น float ได้: {amount_raw}")
            else:
                print("[INFO] amount ว่าง, ไม่บันทึกข้อมูล")
                        
            
        if  request.files:
            count = 0
            if request.files.getlist("formFile_payment"):
                for i, file_PO in enumerate(request.files.getlist("formFile_payment")):
                    if file_PO.filename == '':
                        break
                    target = 'apps/static/assets/files/payment/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    order_code = order_code
                    payment_no = payment_no
                    memver_code = id_member
                    filename = f'SLIP_{order_code}_{payment_no}_{memver_code}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FilePaymentModel(filename=file_name,filepath=file_path,file_type =1, order_id=id_order)
                    db.session.add(newfile)
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
   
    filename_without_ext, file_extension = file.filepath.rsplit('.', 1)
    path = os.path.join("static", "assets", "files", "payment", file.filename)

    # path = "static\\assets\\files\\payment\\" + file.filename   
    file_path = os.path.join(path)    # file = FileModel.query.filter_by(filename=filename).first()
    return send_file(path, as_attachment=True)


@blueprint.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    id_file = request.form["id_file"]
    id_order = request.form["id_order"]

    print(id_order)
    thisFile = FilePaymentModel.query.filter_by(id=id_file).first()

    if not thisFile:  # เช็กว่าเจอรูปหรือไม่
        print(f"ไม่พบรูปภาพที่มี ID: {id_file}")
        return redirect(url_for('order_blueprint.order_update', id=id_order))

    try:
        path = os.path.join("apps", "static", "assets", "files", "payment", thisFile.filename)
        os.remove(path)
    except FileNotFoundError:
        print(f"ไม่พบไฟล์: {path}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")

    # order_id = thisFile.order_id  # ✅ เก็บค่าไว้ก่อนลบ

    db.session.delete(thisFile)
    db.session.commit()

    return redirect(url_for('order_blueprint.order_update', id=id_order))