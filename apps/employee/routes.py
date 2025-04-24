
import time
import re
from apps.employee import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.supplier.models import *
from apps.employee.models import *
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

read_permission = Permission(RoleNeed("read_employee"))
write_permission = Permission(RoleNeed("write_employee"))
delete_permission = Permission(RoleNeed("delete_employee"))


# ---------- Fees ------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def employee():
    datas = EmployeeModel.query.all()
    # print(datas)
    return render_template('employee/employee.html', segment='employee' ,datas=datas, )

@blueprint.route("/get_employee", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_employee():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: EmployeeModel.id,          # คอลัมน์ที่ 0 -> id
        1: EmployeeModel.name,        # คอลัมน์ที่ 1 -> name
        2: EmployeeModel.country_id,  # คอลัมน์ที่ 2 -> description
        3: EmployeeModel.tel # คอลัมน์ที่ 2 -> description
    }

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, EmployeeModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = EmployeeModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # ค้นหาข้อมูล
    search = f"%{search_value}%"

    query = db.session.query(EmployeeModel).\
        outerjoin(CountryModel, CountryModel.id == EmployeeModel.country_id).\
        filter(
            or_(
                EmployeeModel.name.ilike(search),
                CountryModel.name.ilike(search),
                EmployeeModel.tel.ilike(search)
            )
        )

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    employees = query.order_by(column_order).offset(start).limit(length).all()
    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,
        "data_id": employee.id,
        "name": employee.name,
        "country": employee.country.name,
        "tel": employee.tel,
        
    } for index, employee in enumerate(employees)]

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })

@blueprint.route('/addEmployee', methods=['POST'])
@login_required
def addEmployee():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
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
    return jsonify({'status': 'Success', 'message': 'Data has been saved'}), 200

#---------------End Fees------------------------------
    
@blueprint.route('/employee_create')
@login_required
@read_permission.require(http_exception=403)
def employee_create():
    datas = EmployeeModel.query.all()
    countrylist = CountryModel.query.all()
    return render_template('employee/employee_create.html', segment='employee' ,datas=datas,countrylist=countrylist,)   

@blueprint.route('/createEmployee', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def createEmployee():
    print(request.form)
    
    try:
        name_company =request.form.get('n_nameCompany')
        tax =request.form.get('n_tax')
        country =request.form.get('n_country')
        address =request.form.get('address')
        name_coondinator =request.form.get('name_coondinator')
        email =request.form.get('email')
        tel =request.form.get('tel')
        
        
        existing_employee_by_name = EmployeeModel.query.filter_by(name=name_company).first()
        if existing_employee_by_name:
            flash("ชื่อบริษัทซ้ำ: " + existing_employee_by_name.name, "warning")
            return redirect(url_for('employee_blueprint.employee_create'))

        existing_employee_by_tax = EmployeeModel.query.filter_by(tax=tax).first()
        if existing_employee_by_tax:
            flash("เลขผู้เสียภาษีซ้ำ: " + existing_employee_by_tax.tax, "warning")
            return redirect(url_for('employee_blueprint.employee_create'))
        
        # if name_check:
        #     flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        else :
            newItem = EmployeeModel(name=name_company,
                                    tax=tax,
                                    address=address,
                                    tel=tel,
                                    email=email,
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
                    target = 'apps/static/assets/files/employee/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    employee_id = newItem.id
                    filename = f'{employee_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileEmployeeModel(filename=file_name,filepath=file_path,file_type =1, employee_id=newItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('employee_blueprint.employee'))
    
    

 
    
@blueprint.route('/employee_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def employee_update(id):
    datas = EmployeeModel.query.filter_by(id=id).first()
    countrylist = CountryModel.query.all()
    file_data = FileEmployeeModel.query.filter_by(employee_id  = datas.id).all()
    return render_template('employee/employee_update.html', segment='employee' ,datas=datas,countrylist=countrylist,file_data=file_data)    


@blueprint.route('/downloadEmployee/<filename>')
def downloadEmployee(filename):
    
    file = FileEmployeeModel.query.filter_by(filename=filename).first()
   
    filename_without_ext, file_extension = file.filepath.rsplit('.', 1)

    path = "static\\assets\\files\\employee\\" + file.filename   
    file_path = os.path.join(path)    # file = FileModel.query.filter_by(filename=filename).first()
    
    
    return send_file(file_path, as_attachment=True)

@blueprint.route('/employee_delete_file', methods=['POST'])
@login_required
def employee_delete_file():  
    # print(request.form)
    id_file = request.form["id_file"]
    id_employee = request.form["id"]
    thisFile= FileEmployeeModel.query.filter_by(id=id_file).first()
    
    
    if thisFile.file_type == 1:
        try:
            
            path = "apps\\static\\assets\\files\\employee\\" + thisFile.filename
            file_path = os.path.join(path)
            # print(file_path)
            os.remove(file_path)
        except FileNotFoundError:
            print(f"ไม่พบไฟล์: {file_path}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        # thisFile.flag_delete = True
        db.session.query(FileEmployeeModel).filter(FileEmployeeModel.id == id_file).delete()
        db.session.commit()
        

    return redirect(url_for('employee_blueprint.employee_update', id=id_employee))

@blueprint.route('/updateEmployee', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def updateEmployee():
    print(request.form)
    
    try:
        id = request.form.get('id') or None
        name_company =request.form.get('n_nameCompany') or None
        tax =request.form.get('n_tax') or None
        country =request.form.get('n_country') or None
        address =request.form.get('address') or None
        name_coondinator =request.form.get('name_coondinator') or None
        email =request.form.get('email') or None
        tel =request.form.get('tel') or None
            
            
        thisItem = EmployeeModel.query.filter_by(id=id).first()
        
        if thisItem:
            
            if name_company != thisItem.name:
                name_check = EmployeeModel.query.filter_by(name=name_company).first()
                if name_check:
                    flash("ไม่สามารถบันทึกข้อมูลได้: ชื่อซ้ำกับในระบบ", "danger")
                    return redirect(url_for('employee_blueprint.employee'))
                
            thisItem.name=name_company
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
                    target = 'apps/static/assets/files/employee/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    employee_id = thisItem.id
                    filename = f'{employee_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileEmployeeModel(filename=file_name,filepath=file_path,file_type =1, employee_id=thisItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('employee_blueprint.employee_update', id=id))


@blueprint.route('/delete_employee', methods=['POST'])
@login_required
def delete_employee():
    id_del = request.form["id"]

    
    file_list = FileEmployeeModel.query.filter_by(employee_id=id_del).all()

    for file_item in file_list:
        if file_item.file_type == 1:
            try:
                file_path = os.path.join("apps", "static", "assets", "files", "employee", file_item.filename)
                os.remove(file_path)
            except FileNotFoundError:
                print(f"❌ ไม่พบไฟล์: {file_path}")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
    # thisFile.flag_delete = True
    ProductEmployerAssociation.query.filter_by(employee_id=id_del).delete()
    db.session.query(EmployeeModel).filter(EmployeeModel.id == id_del).delete()
    db.session.query(FileEmployeeModel).filter(FileEmployeeModel.employee_id == id_del).delete()
    db.session.commit()
        
    flash(' Deleted!', 'success')
    return redirect(url_for('employee_blueprint.employee'))


@blueprint.route('/list_ProductEmployee')
@login_required
@read_permission.require(http_exception=403)
def list_ProductEmployee():
    datas = EmployeeModel.query.all()
    for employee in datas:
        product_employee = ProductEmployerAssociation.query.filter_by(employee_id=employee.id).first()
    print(datas)
    # print(datas)
    return render_template('employee/list_ProductEmployee.html', segment='list_ProductEmployee' ,datas=datas, )

@blueprint.route("/get_listProductemployee", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listProductemployee():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    Product = aliased(ProductForSalesModel)
    Employee = aliased(EmployeeModel)
    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: Employee.id,          # คอลัมน์ที่ 0 -> id
        1: Employee.name,        # คอลัมน์ที่ 1 -> name
        2: Employee.country_id,  # คอลัมน์ที่ 2 -> description
        3: Employee.tel,         # คอลัมน์ที่ 3 -> tel
        4: Product.name          # คอลัมน์ที่ 4 -> product
    }
    
    # ค้นหาข้อมูล
    query = db.session.query(Employee, Product.name).\
    outerjoin(ProductEmployerAssociation, Employee.id == ProductEmployerAssociation.employee_id).\
    outerjoin(Product, Product.id == ProductEmployerAssociation.product_id).\
    outerjoin(CountryModel, CountryModel.id == Employee.country_id)


    if search_value:
        search = f"%{search_value}%"
        query = query.filter(
            or_(
                Employee.name.ilike(search),
                Employee.tel.ilike(search),
                CountryModel.name.ilike(search),
                Product.name.ilike(search)
            )
        )

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, Employee.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
        query = query.order_by(column_order)
    else:
        query = query.order_by(Employee.id)

    # Pagination
    total_records = query.count()
    query = query.offset(start).limit(length)
    rows = query.all()

    # Group ข้อมูลตาม employee_id
    grouped = {}
    display_index = 1  # 👈 เริ่มนับลำดับที่ 1


    for index, (employee, product_name) in enumerate(rows,start=start):
        employee_id = employee.id

        if employee_id not in grouped:
            grouped[employee_id] = {
                "id": display_index ,
                "data_id": employee.id,
                "name": employee.name,
                "country": employee.country.name if employee.country else "-",
                "tel": employee.tel,
                "product": set()
            }
            display_index += 1 
        if product_name:
            grouped[employee_id]["product"].add(product_name)

    # แปลง set → string และแสดงผลเป็น badge
    data = []
    for employee in grouped.values():
        # สร้าง badge สำหรับแต่ละ product
        employee["product"] = ', '.join(
            [f'<span class="badge bg-info text-white me-1">{p.strip()}</span>' for p in sorted(employee["product"])]
        ) if employee["product"] else "ไม่มีโครงการ"

        data.append(employee)

    # ส่งออกข้อมูล
    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })     
    # # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    # employees = query.order_by(column_order).offset(start).limit(length).all()
    # # แปลงข้อมูลเป็น JSON
    # data = [{
    #     "id": employee.id,
    #     "name": employee.name,
    #     "country": employee.country.name,
    #     "tel": employee.tel,
        
    # } for employee in employees]

    # return jsonify({
    #     "draw": draw,
    #     "recordsTotal": total_records,
    #     "recordsFiltered": total_records,
    #     "data": data
    # })