
import time
import re
from apps.supplier import blueprint
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


# import logging

# logging.basicConfig(filename='error.log', level=logging.ERROR)

read_permission = Permission(RoleNeed("read_supplier"))
write_permission = Permission(RoleNeed("write_supplier"))
delete_permission = Permission(RoleNeed("delete_supplier"))

def model_to_dict(model):
    data = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        if isinstance(value, bytes):  # ตรวจสอบว่าเป็น bytes หรือไม่
            # แปลงเป็น base64 หรือ string
            value = base64.b64encode(value).decode('utf-8')
        data[c.name] = value
    return data
# ---------- Fees ------------------------s
@blueprint.route('/fees')
@login_required
@read_permission.require(http_exception=403)
def fees():
    datas = FeesModel.query.all()
    # print(datas)
    return render_template('supplier/fees.html', segment='fees' ,datas=datas, )

@blueprint.route("/get_fees", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_fees():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    
    column_map = {
    0: FeesModel.id,
    1: FeesModel.name,
    2: FeesModel.description
    }

    # เริ่ม query
    query = FeesModel.query

    # ค้นหาข้อมูล
    if search_value:
        query = query.filter(FeesModel.name.ilike(f"%{search_value}%"))

    # นับจำนวนข้อมูลหลังจาก filter
    total_filtered = query.count()
        
     # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, FeesModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = FeesModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    fees = query.order_by(column_order).offset(start).limit(length).all()

    # นับจำนวนแถวทั้งหมด
    total_records = FeesModel.query.count()


    
    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1 + start,  # เริ่มลำดับตาม start
        "name": fee.name,
        "description": fee.description,
        "data_fee": model_to_dict(fee)
    } for index, fee in enumerate(fees)]

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_filtered,
        "data": data
    })

@blueprint.route('/addFees', methods=['POST'])
@login_required
def addFees():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    print(json_data)

    name =json_data["name"]
    description =json_data["description"]

    if not name:
        flash("Supplier name is required!", "warning")
        return jsonify({'status': 'Error', 'message': 'Supplier name is required!'}), 400

    name_check = FeesModel.query.filter_by(name=name).first()
    
    
    if name_check:
        print("⚠️ พบชื่อซ้ำ:", name_check)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ชื่อซ้ำไม่สามารถบันทึกข้อมูล', "data": name}), 400

        
    else:
        newItem = FeesModel(name=name,description=description)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
        return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200

@blueprint.route('/editFees', methods=['POST'])
@login_required
def editFees():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    print(json_data)
    id_fees = json_data["id"]
    name =json_data["name"]
    description =json_data["description"]

    if not name:
        flash("Supplier name is required!", "warning")
        return jsonify({'status': 'Error', 'message': 'Supplier name is required!'}), 400
        # return redirect(url_for('supplier_blueprint.fees'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = FeesModel.query.filter_by(name=name).first()
    
    if  name_check:
        print("⚠️ พบชื่อซ้ำ:", name_check)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ชื่อซ้ำไม่สามารถบันทึกข้อมูล', "data": name}), 400
        
    else:
        thisItem = FeesModel.query.filter_by(id=id_fees).first()
        thisItem.name = name
        thisItem.description = description
        db.session.commit()
        flash("Edit success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200

@blueprint.route('/delete_fees', methods=['POST'])
@login_required
def delete_fees():
    id_del = request.form["id"]
    print( id_del)
    # thisItem = ProductCategoryModel.query.filter_by(id=id_del).first()
    db.session.query(FeesModel).filter(FeesModel.id == id_del).delete()
    db.session.commit()
    flash(' Deleted!', 'success')
    # return jsonify({'status': 'Success', 'message': 'Data has been saved'}), 200
    return redirect(url_for('supplier_blueprint.fees'))

#---------------End Fees------------------------------
#---------------Supplier Type-------------------------
@blueprint.route('/supplier_type')
@login_required
@read_permission.require(http_exception=403)
def supplier_type():
    datas = SupplierTypeModel.query.all()
    print(datas)
    return render_template('supplier/supplierType.html', segment='supplier_type' ,datas=datas, )

@blueprint.route("/get_supplierType", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_supplierType():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: SupplierTypeModel.id,          # คอลัมน์ที่ 0 -> id
        1: SupplierTypeModel.name,        # คอลัมน์ที่ 1 -> name
        2: SupplierTypeModel.description  # คอลัมน์ที่ 2 -> description
    }

    
    # ค้นหาข้อมูล
    query = SupplierTypeModel.query
    if search_value:
        query = query.filter(SupplierTypeModel.name.ilike(f"%{search_value}%"))

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, FeesModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = SupplierTypeModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order
        
    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    supplier_types = query.order_by(column_order).offset(start).limit(length).all()
    
    # นับจำนวนแถวทั้งหมด
    total_records = SupplierTypeModel.query.count()


    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1 + start,
        "name": supplier_types.name,
        "description": supplier_types.description,
        "data_sup": model_to_dict(supplier_types)
    } for index, supplier_types in enumerate(supplier_types)]

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })

@blueprint.route('/addSupplier', methods=['POST'])
@login_required
def addSupplier():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    print(json_data)

    name =json_data["name"]
    description =json_data["description"]

    if not name:
        flash("Supplier name is required!", "warning")
        return jsonify({'status': 'Error', 'message': 'Supplier name is required!'}), 400

    name_check = SupplierTypeModel.query.filter_by(name=name).first()
    
    
    if name_check:
        print("⚠️ พบชื่อซ้ำ:", name_check)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ชื่อซ้ำไม่สามารถบันทึกข้อมูล', "data": name}), 400

        
    else:
        newItem = SupplierTypeModel(name=name,description=description)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
        return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200
    
@blueprint.route('/editSupplier', methods=['POST'])
@login_required
def editSupplier():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    print(json_data)
    id_fees = json_data["id"]
    name =json_data["name"]
    description =json_data["description"]

    if not name:
        flash("Supplier name is required!", "warning")
        return jsonify({'status': 'Error', 'message': 'Supplier name is required!'}), 400
        # return redirect(url_for('supplier_blueprint.fees'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = SupplierTypeModel.query.filter_by(name=name).first()
    
    if  name_check:
        print("⚠️ พบชื่อซ้ำ:", name_check)  # ✅ ตรวจสอบว่าค่าเข้ามาแล้วจริง
        return jsonify({'status': 'Error', 'message': 'ชื่อซ้ำไม่สามารถบันทึกข้อมูล', "data": name}), 400
        
    else:
        thisItem = SupplierTypeModel.query.filter_by(id=id_fees).first()
        thisItem.name = name
        thisItem.description = description
        db.session.commit()
        flash("Edit success!", "success")
        return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200

@blueprint.route('/deleteSupplier', methods=['POST'])
@login_required
def deleteSupplier():
    id_del = request.form["id"]
    # thisItem = ProductCategoryModel.query.filter_by(id=id_del).first()
    db.session.query(SupplierTypeModel).filter(SupplierTypeModel.id == id_del).delete()
    db.session.commit()
    flash(' Deleted!', 'success')
    return redirect(url_for('supplier_blueprint.supplier_type'))

#--------------------supplier main-------------------
@blueprint.route('/supplier_main')
@login_required
@read_permission.require(http_exception=403)
def supplier_main():
    datas = SupplierModel.query.all()
    for supplier in datas:
        product_supplier = ProductSupplierAssociation.query.filter_by(supplier_id=supplier.id).first()
    print(datas)
    return render_template('supplier/supplier.html', segment='supplier_main' ,datas=datas, )

@blueprint.route("/get_supplier", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_supplier():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

      
    Product = aliased(ProductForSalesModel)
    Supplier = aliased(SupplierModel)

    query = db.session.query(SupplierModel, Product.name)\
        .outerjoin(ProductSupplierAssociation, SupplierModel.id == ProductSupplierAssociation.supplier_id)\
        .outerjoin(Product, Product.id == ProductSupplierAssociation.product_id)

    # Mapping คอลัมน์จาก DataTable ไปยังฟิลด์ในฐานข้อมูล
    column_map = {
        0: SupplierModel.id,
        1: SupplierModel.name,
        2: SupplierModel.supplierType_id,
        3: SupplierModel.country_id,
        4: SupplierModel.tel,
        5: Product.name
    }

    # การค้นหา
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                SupplierModel.name.ilike(search),
                Product.name.ilike(search)
            )
        )

    # การจัดเรียง
    if order:
        column_index = int(order[0]["column"])
        column_order = column_map.get(column_index, SupplierModel.id)
        sort_direction = order[0]["dir"]

        if sort_direction == "desc":
            column_order = column_order.desc()
        query = query.order_by(column_order)
    else:
        query = query.order_by(SupplierModel.id)

    # Pagination
    total_records = query.count()
    query = query.offset(start).limit(length)
    rows = query.all()

    # รวม product ด้วย supplier_id
    grouped = {}

    for index, (supplier, product_name) in enumerate(rows, start=start):
        supplier_id = supplier.id

        if supplier_id not in grouped:
            grouped[supplier_id] = {
                "id": index + 1,
                "data_id": supplier.id,
                "name": supplier.name,
                "supplier_type": supplier.supplier_type.name if supplier.supplier_type else "-",
                "country": supplier.country.name if supplier.country else "-",
                "tel": supplier.tel,
                "product": set()
            }

        if product_name:
            grouped[supplier_id]["product"].add(product_name)

    # แปลง set → string
    data = []
    for supplier in grouped.values():
        supplier["product"] = ', '.join(sorted(supplier["product"])) if supplier["product"] else "-"
        data.append(supplier)

    # ส่งออก
    return jsonify({
        "draw": draw,
                "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })                  
    
    
@blueprint.route('/supplier_create')
@login_required
@read_permission.require(http_exception=403)
def supplier_create():
    datas = SupplierModel.query.all()
    supplierTypelist = SupplierTypeModel.query.all()
    countrylist = CountryModel.query.all()
    return render_template('supplier/supplier_create.html', segment='supplier' ,datas=datas, supplierTypelist=supplierTypelist,countrylist=countrylist,)   

@blueprint.route('/createMainSupplier', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def createMainSupplier():
    print(request.form)
    
    try:
        name_company =request.form.get('n_nameCompany')
        supplierType =request.form.get('supplierType')
        tax =request.form.get('n_tax')
        country =request.form.get('n_country')
        address =request.form.get('address')
        name_coondinator =request.form.get('name_coondinator')
        email =request.form.get('email')
        tel =request.form.get('tel')
        
        
        # name_check = SupplierModel.query.filter_by(name=name_company).first()
        # ตรวจสอบว่ามี supplier ที่ซ้ำไหม
        # existing_supplier = SupplierModel.query.filter(
        #     or_(
        #         SupplierModel.name == name_company,
        #         SupplierModel.tax == tax,
        #         # SupplierModel.email == email,
        #         # SupplierModel.tel == tel
        #     )
        # ).first()

        # if existing_supplier:
        #     flash("มี Supplier ที่ข้อมูลซ้ำอยู่แล้วในระบบ", "warning")
        #     return redirect(url_for('supplier_blueprint.supplier_create'))
        
        existing_supplier_by_name = SupplierModel.query.filter_by(name=name_company).first()
        if existing_supplier_by_name:
            flash("ชื่อบริษัทซ้ำ: " + existing_supplier_by_name.name, "warning")
            return redirect(url_for('supplier_blueprint.supplier_create'))

        existing_supplier_by_tax = SupplierModel.query.filter_by(tax=tax).first()
        if existing_supplier_by_tax:
            flash("เลขผู้เสียภาษีซ้ำ: " + existing_supplier_by_tax.tax, "warning")
            return redirect(url_for('supplier_blueprint.supplier_create'))
        # if name_check:
        #     flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        else :
            newItem = SupplierModel(name=name_company,
                                    tax=tax,
                                    address=address,
                                    tel=tel,
                                    email=email,
                                    supplierType_id=supplierType,
                                    country_id=country,
                                    name_coondinator=name_coondinator
                                    )
            db.session.add(newItem)
            db.session.commit()
            flash("Add success!", "success")
            
        if  request.files:
            count = 0
            if request.files.getlist("formFile"):
                for i, file_PO in enumerate(request.files.getlist("formFile")):
                    if file_PO.filename == '':
                        break
                    target = 'apps/static/assets/files/supplier/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    supplier_id = newItem.id
                    filename = f'{supplier_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileSupplierModel(filename=file_name,filepath=file_path,file_type =1, supplier_id=newItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('supplier_blueprint.supplier_main'))
    
    

 
    
@blueprint.route('/supplier_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def supplier_update(id):
    datas = SupplierModel.query.filter_by(id=id).first()
    supplierTypelist = SupplierTypeModel.query.all()
    countrylist = CountryModel.query.all()
    file_data = FileSupplierModel.query.filter_by(supplier_id  = datas.id).all()
    return render_template('supplier/supplier_update.html', segment='supplier_main' ,datas=datas, supplierTypelist=supplierTypelist,countrylist=countrylist,file_data=file_data)    


@blueprint.route('/downloadSupplier/<filename>')
def downloadSupplier(filename):
    
    file = FileSupplierModel.query.filter_by(filename=filename).first()
   
    filename_without_ext, file_extension = file.filepath.rsplit('.', 1)

    path = "static\\assets\\files\\supplier\\" + file.filename+'.'+file_extension   
    file_path = os.path.join(path)    # file = FileModel.query.filter_by(filename=filename).first()
    
    
    return send_file(file_path, as_attachment=True)

@blueprint.route('/supplier_delete_file', methods=['POST'])
@login_required
def supplier_delete_file():  
    # print(request.form)
    id_file = request.form["id_file"]
    id_supplier = request.form["id"]
    thisFile= FileSupplierModel.query.filter_by(id=id_file).first()
    
    
    if thisFile.file_type == 1:
        try:
            
            path = "apps\\static\\assets\\files\\supplier\\" + thisFile.filename
            file_path = os.path.join(path)
            # print(file_path)
            os.remove(file_path)
        except FileNotFoundError:
            print(f"ไม่พบไฟล์: {file_path}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        # thisFile.flag_delete = True
        db.session.query(FileSupplierModel).filter(FileSupplierModel.id == id_file).delete()
        db.session.commit()
        

    return redirect(url_for('supplier_blueprint.supplier_update', id=id_supplier))

@blueprint.route('/updateMainSupplier', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def updateMainSupplier():
    print(request.form)
    
    try:
        id = request.form.get('id') or None
        name_company =request.form.get('n_nameCompany') or None
        supplierType =request.form.get('supplierType') or None
        tax =request.form.get('n_tax') or None
        country =request.form.get('n_country') or None
        address =request.form.get('address') or None
        name_coondinator =request.form.get('name_coondinator') or None
        email =request.form.get('email') or None
        tel =request.form.get('tel') or None
            
       
            
        thisItem = SupplierModel.query.filter_by(id=id).first()
        
        if thisItem:
            
            # เช็คชื่อใหม่ซ้ำกับคนอื่นหรือไม่
            if name_company != thisItem.name:
                name_check = SupplierModel.query.filter(
                    SupplierModel.name == name_company,
                    SupplierModel.id != thisItem.id  # ไม่เช็คกับตัวเอง
                ).first()
                if name_check:
                    flash("ไม่สามารถบันทึกข้อมูลได้: ชื่อบริษัทซ้ำกับในระบบ", "danger")
                    return redirect(url_for('supplier_blueprint.supplier_main'))

            # เช็ค tax ใหม่ซ้ำกับคนอื่นหรือไม่
            if tax != thisItem.tax:
                tax_check = SupplierModel.query.filter(
                    SupplierModel.tax == tax,
                    SupplierModel.id != thisItem.id
                ).first()
                if tax_check:
                    flash("ไม่สามารถบันทึกข้อมูลได้: เลขประจำตัวผู้เสียภาษีซ้ำกับในระบบ", "danger")
                    return redirect(url_for('supplier_blueprint.supplier_main'))

            
                
            thisItem.name=name_company
            thisItem.supplierType_id=supplierType
            thisItem.tax=tax
            thisItem.country_id=country
            thisItem.address=address  
            thisItem.name_coondinator=name_coondinator 
            thisItem.email=email
            thisItem.tel=tel
            db.session.commit()
            flash("Update success!", "success")
        
            
        if  request.files:
            count = 0
            if request.files.getlist("formFile"):
                for i, file_PO in enumerate(request.files.getlist("formFile")):
                    if file_PO.filename == '':
                        break
                    target = 'apps/static/assets/files/supplier/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    supplier_id = thisItem.id
                    filename = f'{supplier_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileSupplierModel(filename=file_name,filepath=file_path,file_type =1, supplier_id=thisItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('supplier_blueprint.supplier_update', id=id))


@blueprint.route('/delete_supplierMain', methods=['POST'])
@login_required
def delete_supplierMain():
    id_del = request.form["id"]

    
    file_list = FileSupplierModel.query.filter_by(supplier_id=id_del).all()

    for file_item in file_list:
        if file_item.file_type == 1:
            try:
                file_path = os.path.join("apps", "static", "assets", "files", "supplier", file_item.filename)
                os.remove(file_path)
            except FileNotFoundError:
                print(f"❌ ไม่พบไฟล์: {file_path}")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
    # thisFile.flag_delete = True
    db.session.query(SupplierModel).filter(SupplierModel.id == id_del).delete()
    db.session.query(FileSupplierModel).filter(FileSupplierModel.supplier_id == id_del).delete()
    ProductSupplierAssociation.query.filter_by(supplier_id=id_del).delete()

    db.session.commit()
        
    flash(' Deleted!', 'success')
    return redirect(url_for('supplier_blueprint.supplier_main'))

@blueprint.route('/list_Productsupplier')
@login_required
@read_permission.require(http_exception=403)
def list_Productsupplier():
    datas = SupplierModel.query.all()
    for supplier in datas:
        product_supplier = ProductSupplierAssociation.query.filter_by(supplier_id=supplier.id).first()
    print(datas)
    return render_template('supplier/list_ProductSupplier.html', segment='list_Productsupplier' ,datas=datas, )

@blueprint.route("/get_Productsupplier", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_Productsupplier():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    
    Product = aliased(ProductForSalesModel)
    Supplier = aliased(SupplierModel)

    query = db.session.query(SupplierModel, Product.name)\
        .outerjoin(ProductSupplierAssociation, SupplierModel.id == ProductSupplierAssociation.supplier_id)\
        .outerjoin(Product, Product.id == ProductSupplierAssociation.product_id)

    # Mapping คอลัมน์จาก DataTable ไปยังฟิลด์ในฐานข้อมูล
    column_map = {
        0: SupplierModel.id,
        1: SupplierModel.name,
        2: SupplierModel.supplierType_id,
        3: SupplierModel.country_id,
        4: SupplierModel.tel,
        5: Product.name
    }

    # การค้นหา
    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                SupplierModel.name.ilike(search),
                Product.name.ilike(search)
            )
        )

    # การจัดเรียง
    if order:
        column_index = int(order[0]["column"])
        column_order = column_map.get(column_index, SupplierModel.id)
        sort_direction = order[0]["dir"]

        if sort_direction == "desc":
            column_order = column_order.desc()
        query = query.order_by(column_order)
    else:
        query = query.order_by(SupplierModel.id)

    # Pagination
    total_records = query.count()
    query = query.offset(start).limit(length)
    rows = query.all()

    # รวม product ด้วย supplier_id
    grouped = {}
    display_index = 1 
    for supplier, product_name in rows:
        supplier_id = supplier.id

        if supplier_id not in grouped:
            grouped[supplier_id] = {
                "id": display_index,
                "data_id": supplier.id,
                "name": supplier.name,
                "supplier_type": supplier.supplier_type.name if supplier.supplier_type else "-",
                "country": supplier.country.name if supplier.country else "-",
                "tel": supplier.tel,
                "product": set()
            }
            display_index += 1
        if product_name:
            grouped[supplier_id]["product"].add(product_name)

    # แปลง set → string
    data = []
    for supplier in grouped.values():
        # supplier["product"] = ', '.join(sorted(supplier["product"])) if supplier["product"] else "-ไม่มีโครงการ"
        # supplier["product"] = ', '.join(sorted(supplier["product"])) if supplier["product"] else "-ไม่มีโครงการ"
        supplier["product"] = ', '.join(
            [f'<span class="badge bg-info text-white me-1">{p.strip()}</span>' for p in sorted(supplier["product"])]
        ) if supplier["product"] else "ไม่มีโครงการ"
        data.append(supplier)

    # ส่งออก
    return jsonify({
        "draw": draw,
                "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })             