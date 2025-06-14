
import time
import re
from apps.product import blueprint
from apps.authentication.models import *
from apps.organization.models import *
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
from sqlalchemy import and_, func, case, asc
from collections import defaultdict

from decimal import Decimal




read_permission = Permission(RoleNeed("read_permission"))
write_permission = Permission(RoleNeed("write_permission"))
delete_permission = Permission(RoleNeed("delete_permission"))

@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = PermissionModel.query.all()
    resources = ResourceModel.query.all()
    # print(datas)
    return render_template('usermanage/permission.html', segment='permission' ,datas=datas, resources=resources)

@blueprint.route('/product_category')
@login_required
@read_permission.require(http_exception=403)
def product_category():
    datas = ProductCategoryModel.query.all()
    # print(datas)
    return render_template('product/product_category.html', segment='product_category' ,datas=datas)

@blueprint.route('/product/add_productCategory', methods=['POST'])
@login_required
def add_product_category():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    
    print(json_data)

    name_product =json_data["name_product"]
    print(name_product)

    if not name_product:
        flash("Product name is required!", "warning")
        return redirect(url_for('product_blueprint.product_category'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = ProductCategoryModel.query.filter_by(name=name_product).first()
    
    if  name_check:
        flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        
    else:
        newItem = ProductCategoryModel(name=name_product)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200
    


@blueprint.route('/product/edit_productCategory', methods=['POST'])
@login_required
def edit_productCategory():
    json_data = request.get_json()

    thisItem = ProductCategoryModel.query.filter_by(id=json_data['id']).first()
    thisItem.name = json_data['name_product']
    
    db.session.commit()
    flash("Update success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":thisItem}), 200

@blueprint.route('/product/delete_productCategory', methods=['POST'])
@login_required
def delete_productCategory():
    id_del = request.form["id"]
    print( id_del)
    # thisItem = ProductCategoryModel.query.filter_by(id=id_del).first()
    db.session.query(ProductForSalesModel).filter(ProductForSalesModel.id == id_del).delete()
    db.session.commit()
    flash(' Deleted!', 'success')
    return redirect(url_for('product_blueprint.productSales'))



@blueprint.route('/add', methods=['POST'])
@login_required
def add():
    print(request.form)
    name = request.form.get("name")
    description = request.form.get("description")
    resource_id = request.form.get("resource_id")
    name_check = PermissionModel.query.filter_by(name=name).filter_by(resource_id=resource_id).first()
    if not name_check :
        newItem = PermissionModel(name=name, description=description, resource_id=resource_id)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    else:
        flash("Already registered!", "danger")
    return redirect(url_for('permission_blueprint.index'))



@blueprint.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    thisItem = PermissionModel.query.filter_by(id=id).first()
    name = thisItem.name
    resource = thisItem.resource.name
    db.session.query(PermissionModel).filter(
        PermissionModel.id == id).delete()
    db.session.commit()
    flash(name+' '+resource+' Deleted!', 'success')
    return redirect(url_for('permission_blueprint.index'))

@blueprint.route('/update', methods=['POST'])
@login_required
def update():
    # print(request.form)
    id = request.form["id"]
    name = request.form["name"]
    description = request.form["description"]
    resource_id = request.form["resource_id"]
    name_check = PermissionModel.query.filter_by(name=name).filter_by(resource_id=resource_id).first()
    if name_check:
        if name_check.id != int(id):
            flash("Already registered!", "danger")
            return redirect(url_for('permission_blueprint.index'))
    thisItem = PermissionModel.query.filter_by(id=id).first()
    thisItem.name = name
    thisItem.description = description
    db.session.commit()
    flash("Update success!", "success")
    return redirect(url_for('permission_blueprint.index'))

@blueprint.route('/country')
@login_required
@read_permission.require(http_exception=403)
def country():
    datas = CountryModel.query.all()
    # print(datas)
    return render_template('product/country.html', segment='country' ,datas=datas)


@blueprint.route('/product/addcountry', methods=['POST'])
@login_required
def addcountry():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    
    print(json_data)

    name =json_data["name"]
    print(name)

    if not name:
        flash("Country name is required!", "warning")
        return redirect(url_for('product_blueprint.country'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = CountryModel.query.filter_by(name=name).first()
    
    if  name_check:
        flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        
    else:
        newItem = CountryModel(name=name)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200
    

@blueprint.route('/product/editCountry', methods=['POST'])
@login_required
def editCountry():
    json_data = request.get_json()

    thisItem = CountryModel.query.filter_by(id=json_data['id']).first()
    thisItem.name = json_data['name']
    
    db.session.commit()
    flash("Update success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":thisItem}), 200

@blueprint.route('/product/deleteCountry', methods=['POST'])

@login_required
def deleteCountry():
    id_del = request.form["id"]
    print( id_del)
    thisItem = CountryModel.query.filter_by(id=id_del).first()
    name = thisItem.name
    db.session.query(CountryModel).filter(CountryModel.id == id_del).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('product_blueprint.country'))



@blueprint.route('/period')
@login_required
@read_permission.require(http_exception=403)
def period():
    datas = PeriodModel.query.all()
    # print(datas)
    return render_template('product/period.html', segment='period' ,datas=datas)

@blueprint.route('/product/addPeriod', methods=['POST'])
@login_required
def addPeriod():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    
    print(json_data)

    name =json_data["name"]
    print(name)

    if not name:
        flash("Period name is required!", "warning")
        return redirect(url_for('product_blueprint.period'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = PeriodModel.query.filter_by(name=name).first()
    
    if  name_check:
        flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        
    else:
        newItem = PeriodModel(name=name)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200
    

@blueprint.route('/product/editPeriod', methods=['POST'])
@login_required
def editPeriod():
    json_data = request.get_json()

    thisItem = PeriodModel.query.filter_by(id=json_data['id']).first()
    thisItem.name = json_data['name']
    
    db.session.commit()
    flash("Update success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":thisItem}), 200

@blueprint.route('/product/deletePeriod', methods=['POST'])

@login_required
def deletePeriod():
    id_del = request.form["id"]
    print( id_del)
    thisItem = PeriodModel.query.filter_by(id=id_del).first()
    name = thisItem.name
    db.session.query(PeriodModel).filter(PeriodModel.id == id_del).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('product_blueprint.period'))


@blueprint.route('/termOfPayment')
@login_required
@read_permission.require(http_exception=403)
def termOfPayment():
    datas = term_of_paymentModel.query.all()
    # print(datas)
    return render_template('product/termOfPayment.html', segment='termOfPayment' ,datas=datas)


@blueprint.route('/product/addTerm', methods=['POST'])
@login_required
def addTerm():  # ✅ แก้ไขชื่อฟังก์ชันให้สอดคล้องกับ URL
    
    json_data = request.get_json()
    name =json_data["name"]

    if not name:
        flash("Term of payment name is required!", "warning")
        return redirect(url_for('product_blueprint.termOfPayment'))  # ✅ แก้ชื่อ route

    # ตรวจสอบว่ามีชื่อซ้ำหรือไม่
    name_check = term_of_paymentModel.query.filter_by(name=name).first()
    
    if  name_check:
        flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        
    else:
        newItem = term_of_paymentModel(name=name)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":name_check}), 200
    

@blueprint.route('/product/editTerm', methods=['POST'])
@login_required
def editTerm():
    json_data = request.get_json()

    thisItem = term_of_paymentModel.query.filter_by(id=json_data['id']).first()
    thisItem.name = json_data['name']
    
    db.session.commit()
    flash("Update success!", "success")
    return jsonify({'status': 'Success', 'message': 'Data has been saved', "data":thisItem}), 200

@blueprint.route('/product/deleteTerm', methods=['POST'])

@login_required
def deleteTerm():
    id_del = request.form["id"]
    print( id_del)
    thisItem = term_of_paymentModel.query.filter_by(id=id_del).first()
    name = thisItem.name
    db.session.query(term_of_paymentModel).filter(term_of_paymentModel.id == id_del).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('product_blueprint.termOfPayment'))


@blueprint.route('/productSales')
@login_required
@read_permission.require(http_exception=403)
def productSales():
    datas = ProductForSalesModel.query.all()
    # print(datas)
    return render_template('/product/productSales.html', segment='productSales' ,datas=datas)

@blueprint.route('/createProductSales')
@login_required
@read_permission.require(http_exception=403)
def createProductSales():
    productCar = ProductCategoryModel.query.all()
    country = CountryModel.query.order_by(asc(CountryModel.name)).all()
    period = PeriodModel.query.all()
    termOfPaymentModel = term_of_paymentModel.query.order_by(term_of_paymentModel.name).all()
    organization = OrganizationModel.query.order_by(OrganizationModel.name).all()
    employee = EmployeeModel.query.order_by(EmployeeModel.name).all()
    # agency = AgencyModel.query.order_by(AgencyModel.agency_code).all()
    # agency = AgencyModel.query.order_by(AgencyModel.agency_code).all()
    
    agency = AgencyModel.query.filter(AgencyModel.org_type == 'agency').all()
    university = AgencyModel.query.filter(AgencyModel.org_type == 'university').all()
    current_year=datetime.now().year
    

    return render_template('/productForSales/createProductSales.html', segment='productSales' ,productCars=productCar, countrys=country, periods=period,termOfPaymentModels=termOfPaymentModel,organizations=organization,employees=employee,agencys=agency,universitys=university,
                           current_year=current_year,groupedPayments=[])

@blueprint.route('/EditProductSales/<id>')
@login_required
@read_permission.require(http_exception=403)
def EditProductSales(id):

    datas= ProductForSalesModel.query.filter_by(id=id).first()
    productCar = ProductCategoryModel.query.all()
    country = CountryModel.query.order_by(asc(CountryModel.name)).all()
    period = PeriodModel.query.all()
    termOfPaymentModel = term_of_paymentModel.query.order_by(term_of_paymentModel.name).all()
    file_data = FileModel.query.filter_by(product_for_sales_id = datas.id).all()
    payment = installmentsPaymentModel.query.filter_by(product_for_sales_id=datas.id).all()
    organization = OrganizationModel.query.order_by(OrganizationModel.name).all()
    employee = EmployeeModel.query.order_by(EmployeeModel.name).all()
    # agency = AgencyModel.query.order_by(AgencyModel.agency_code).all()
    agency = AgencyModel.query.filter(AgencyModel.org_type == 'agency').all()
    university = AgencyModel.query.filter(AgencyModel.org_type == 'university').all()
    
    productSup = ProductOrganizationAssociation.query.filter_by(product_id=id).all()
    selected_organizations = [p.organization_id for p in productSup]
    
    productEmplo = ProductEmployerAssociation.query.filter_by(product_id=id).all()
    selected_employee = [e.employee_id for e in productEmplo]
    
    productAgency = ProductAgencyAssociation.query.filter_by(product_id=id).all()
    selected_agency = [e.agency_id for e in productAgency]
    
    grouped_payments = defaultdict(list)
    for p in payment:
        grouped_payments[p.year].append(p)
    print(grouped_payments)

    return render_template('/productForSales/EditProductSales.html', segment='productSales' , datas=datas, productCars=productCar, countrys=country, periods=period,termOfPaymentModels=termOfPaymentModel, file_data=file_data,payments=payment,organizations=organization,employees=employee,selected_organizations=selected_organizations,selected_employee=selected_employee,selected_agencys=selected_agency,agencys=agency,universitys=university,
                           grouped_payments=grouped_payments)

@blueprint.route('/addProductSale', methods=['GET', 'POST'])
@login_required
@read_permission.require(http_exception=403)
def addProductSale():
    print(request.form)
    # รับค่าจาก request.form
    # ✅ ตรวจสอบค่าจาก request.form
    name = request.form.get('name_product') or None
    year = request.form.get('selectedYear') or ''
    
    price = request.form.get('price') or None
    product_category_id = request.form.get('productCategory') or None
    country_id = request.form.get('country') or None
    period_id = request.form.get('period') or None
    term_of_payment_id = request.form.get('term') or None
    detail = request.form.get('detail') or None
    inputYear = request.form.get('inputYear') or None
    # start = datetime.strptime(request.form.get("start"), "%d-%m-%Y") if request.form["start"] else None 
    # end = datetime.strptime(request.form.get("end"), "%d-%m-%Y") if request.form["end"] else None 
    # ✅ ตรวจสอบว่า country_id และ period_id ได้ค่าที่ถูกต้อง (ต้องเป็นตัวเลข ไม่ใช่ function)
    organization_ids = request.form.getlist('organization') or None
    employee_ids = request.form.getlist('employee') or None
    university_ids = request.form.getlist('university') or None
    agency_ids = request.form.getlist('agency') or None
    
    price_str = request.form.get(f'price_{year}', '0').replace(',', '')
    price = Decimal(price_str or '0')
        
    # term_of_payment_id = request.form.get('term') or None

    

    
    try:
        country_id = int(country_id) if country_id and country_id.isdigit() else None
        period_id = int(period_id) if period_id and period_id.isdigit() else None
        product_category_id = int(product_category_id) if product_category_id and product_category_id.isdigit() else None
        # term_of_payment_id = int(term_of_payment_id) if term_of_payment_id and term_of_payment_id.isdigit() else None
    except Exception as e:
        return jsonify({"error": "Invalid data format"}), 400  # ส่ง error กลับถ้าค่าผิด
    
    # ถ้าค่าที่ได้จากฟอร์มเป็นค่าว่าง หรือ '0' หรือ None จะตั้งเป็น None
    if not term_of_payment_id or term_of_payment_id == '0':
        term_of_payment_id = None

    # ตรวจสอบว่าค่าของ term_of_payment_id เป็น None หรือไม่
    if term_of_payment_id:
        # ตรวจสอบว่า term_of_payment_id นี้มีอยู่ในฐานข้อมูลหรือไม่
        existing_term = term_of_paymentModel.query.filter_by(id=term_of_payment_id).first()
        if not existing_term:
            print(f"Invalid term_of_payment_id: {term_of_payment_id}. Setting to None.")
            term_of_payment_id = None

    
    new_item = ProductForSalesModel(
        name=name,
        year=inputYear,
        price=price,
        product_category_id=product_category_id,
        country_id=country_id,  # ✅ แก้ไขให้ country_id เป็น int หรือ None
        period_id=period_id,  # ✅ แก้ไขให้ period_id เป็น int หรือ None
        term_of_payment_id=term_of_payment_id,
        detail=detail,
        # start_at=start,
        # end_at=end,
    )

    # ✅ เพิ่มข้อมูลลงฐานข้อมูล
    db.session.add(new_item)
    db.session.commit()
        
    try:
        db.session.add(new_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
        
    uploaded_images  = request.files.getlist("formFile_img")
    if uploaded_images:
        image_directory = os.path.join("apps", "static", "assets", "img", "product")
        os.makedirs(image_directory, exist_ok=True)  # สร้างโฟลเดอร์ถ้ายังไม่มี

        for img in uploaded_images:
            if img.filename:  # ตรวจสอบว่ามีชื่อไฟล์
                # ✅ สร้างชื่อไฟล์ใหม่แบบ UUID
                filename = f"{uuid.uuid4().hex}.{img.filename.split('.')[-1]}"
                file_path = os.path.join(image_directory, filename)

                # ✅ บันทึกไฟล์ลงในโฟลเดอร์
                img.save(file_path)

                # # ✅ ค้นหารูปภาพเดิม ถ้าไม่มีให้สร้างใหม่
                # thisItemimg = MD_Image.query.filter_by(product_for_sales_id=new_item.id).first()
                # if thisItemimg:
                #     thisItemimg.image = filename  # ✅ อัปเดตชื่อไฟล์ภาพ
                # else:
                new_image = MD_Image(image=filename, product_for_sales_id=new_item.id)
                db.session.add(new_image)

        db.session.commit()  # ✅ บันทึกการเปลี่ยนแปลง


        
    uploaded_files = request.files.getlist("formFile_file")    
    if  uploaded_files:
        count = 0
        if request.files.getlist("formFile_file"):
            for i, file_qu in enumerate(request.files.getlist("formFile_file")):
                if file_qu.filename == '':
                    break
                target = 'apps/static/assets/files/'
                os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                ftype = file_qu.filename.split('.')
                id_order = new_item.id
                filename = f'{id_order}_{ftype[0]}_{i}'
                file_name = filename + '.' + ftype[-1]

                file_path = os.path.join(target, file_name)
                # print(file_path)
                try:
                    file_qu.save(file_path)  # บันทึกไฟล์
                except Exception as e:
                    return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                count += 1
                newfile = FileModel(filename=filename,filepath=file_path,file_type =1, product_for_sales_id=new_item.id)
                db.session.add(newfile)
                db.session.commit()    
                
    term_years = request.form.getlist('term_year[]')
    
    
    

    for year in term_years:
        ids = request.form.getlist(f'term_id_{year}[]')
        amounts = request.form.getlist(f'installments_{year}[]')
        details = request.form.getlist(f'term_detail_{year}[]')
        price_str = request.form.get(f'price_{year}', '0').replace(',', '')
        price = Decimal(price_str or '0')
        

        raw_vats = request.form.getlist(f'check_vat_{year}[]')

        # กลุ่มทีละ 2 ค่า (hidden, checkbox) → เอา '1' ถ้ามี, ไม่งั้น '0'
        check_vats = []
        for i in range(0, len(raw_vats), 2):
            vat_pair = raw_vats[i:i+2]
            check_vats.append('1' in vat_pair)

        print("check_vats:", check_vats)


        for i in range(len(amounts)):
            amount = Decimal(amounts[i].replace(',', ''))
            detail = details[i].strip()
            term_id = ids[i].strip() if i < len(ids) else None
            check_vat = check_vats[i]

            if term_id:
                existing = installmentsPaymentModel.query.filter_by(id=term_id).first()
                if existing:
                    existing.term_detail = detail
                    existing.amount = amount
                    existing.year = year
                    existing.price = price
                    existing.check_vat = check_vat
                    continue

        
            db.session.add(installmentsPaymentModel(
                term_detail=detail,
                amount=amount,
                year=year,
                price=price,
                product_for_sales_id=new_item.id,
                check_vat=check_vat
            ))

    db.session.commit()
    
    # installments_list = request.form.getlist('installments')  
    # term_detail_list = request.form.getlist('term_detail') 
    # term_id_list = request.form.getlist('term_id')
    
    # db.session.query(installmentsPaymentModel).filter(installmentsPaymentModel.product_for_sales_id == new_item.id).delete()
    # db.session.commit()

   
    
    # # ตรวจสอบว่าลิสต์ไม่ว่าง และมีขนาดเท่ากัน
    # if term_detail_list and installments_list and len(term_detail_list) == len(installments_list):
    #     for i, (term, amount) in enumerate(zip(term_detail_list, installments_list)):
    #         term = term.strip()  # ลบช่องว่าง
    #         amount = str(amount).strip()  # ลบช่องว่าง
    #         amount = amount.replace(',', '')
            
    #         if term_id_list and i < len(term_id_list) and term_id_list[i].strip():  # เช็คว่ามี term_id หรือไม่
    #             term_id = term_id_list[i].strip()
    #             existing_item = installmentsPaymentModel.query.filter_by(id=term_id).first()

    #             if existing_item:  
    #                 print(f"Updating: term_id={term_id}, term_detail={term}, amount={amount}")
    #                 existing_item.term_detail = term
    #                 existing_item.amount = amount
    #             else:  # 
    #                 print(f"Adding new (term_id not found): term_detail={term}, amount={amount}")
    #                 new_payment= installmentsPaymentModel(
    #                     term_detail=term,
    #                     amount=amount,
    #                     product_for_sales_id=new_item.id,
    #                 )
    #                 db.session.add(new_payment)

    #         else: 
    #             print(f"Adding new: term_detail={term}, amount={amount}")
    #             new_payment = installmentsPaymentModel(
    #                 term_detail=term,
    #                 amount=amount,
    #                 product_for_sales_id=new_item.id,
    #             )
    #             db.session.add(new_payment)

    #     db.session.commit()
    #     print("All data saved successfully!")  # แจ้งเตือนว่าเซฟสำเร็จ
    # else:
    #     print("Error: term_detail_list and installments_list do not match in length.")    
        
    if organization_ids:
        for organization_id in organization_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_association = ProductOrganizationAssociation(
                product_id=new_item.id,
                organization_id=organization_id,
            )

            db.session.add(new_association)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Supplier เข้าโครงการสำเร็จ")         
           
    if employee_ids:
        for employee_id in employee_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_associationEmployee = ProductEmployerAssociation(
                product_id=new_item.id,
                employee_id=employee_id,
            )

            db.session.add(new_associationEmployee)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Employee เข้าโครงการสำเร็จ")    
                
    if university_ids:
        for university_id in university_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_associationAgency = ProductAgencyAssociation(
                product_id=new_item.id,
                agency_id=university_id,
            )

            db.session.add(new_associationAgency)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Agency เข้าโครงการสำเร็จ")    
                
    if agency_ids:
        for agency_id in agency_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_associationAgency = ProductAgencyAssociation(
                product_id=new_item.id,
                agency_id=agency_id,
            )

            db.session.add(new_associationAgency)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Agency เข้าโครงการสำเร็จ")            
    # print(datas)
    return redirect(url_for('product_blueprint.EditProductSales',id=new_item.id))

def get_all_check_vat_values(term_years):
    # อ่าน checkbox ตัวเดียว
    single_check_vat = request.form.get('check_vat')
    single_checked = single_check_vat == '1' or single_check_vat == 'on'  # กรณี checkbox ส่งค่า 'on'

    # อ่าน checkbox เป็น list แยกตามปี
    check_vat_years = {}
    for year in term_years:
        raw_vats = request.form.getlist(f'check_vat_{year}[]')
        check_vats = []
        for i in range(0, len(raw_vats), 2):
            vat_pair = raw_vats[i:i+2]
            check_vats.append('1' in vat_pair)
        check_vat_years[year] = check_vats

    return {
        'single': single_checked,
        'by_year': check_vat_years
    }


@blueprint.route('/updateProductSale', methods=['GET', 'POST'])
@login_required
@read_permission.require(http_exception=403)
def updateProductSale():
    print(request.form)
    # รับค่าจาก request.form
    id = request.form.get('id') or None
    name = request.form.get('name_product') or None
    year = request.form.get('selectedYear') or ''
    # price = request.form.get('price') or None
    product_category_id = request.form.get('productCategory') or None
    country_id = request.form.get('country') or None
    period_id = request.form.get('period') or None
    term_of_payment_id = request.form.get('term') or None
    organization_ids = request.form.getlist('organization') or None
    employee_ids = request.form.getlist('employee') or None
    university_ids = request.form.getlist('university') or None
    agency_ids = request.form.getlist('agency') or None
    
    detail = request.form.get('detail') or None
    # start = datetime.strptime(request.form.get("start"), "%d-%m-%Y") if request.form["start"] else None 
    # end = datetime.strptime(request.form.get("end"), "%d-%m-%Y") if request.form["end"] else None
    
    # if price:
    #     price = float(price.replace(',', ''))  # 
    # else:
    #     price = None 
        
    try:
        country_id = int(country_id) if country_id and country_id.isdigit() else None
        period_id = int(period_id) if period_id and period_id.isdigit() else None
        product_category_id = int(product_category_id) if product_category_id and product_category_id.isdigit() else None
        term_of_payment_id = int(term_of_payment_id) if term_of_payment_id and term_of_payment_id.isdigit() else None
    except Exception as e:
        return jsonify({"error": "Invalid data format"}), 400  # ส่ง error กลับถ้าค่าผิด

    # 
    
    price_str = request.form.get(f'price_{year}', '0').replace(',', '')
    price = Decimal(price_str or '0')

    thisItem = ProductForSalesModel.query.filter_by(id=id).first()
    if thisItem:
        thisItem.name=name,
        thisItem.year=year,
        thisItem.price=price,
        thisItem.product_category_id=product_category_id,
        thisItem.country_id=country_id,  
        thisItem.period_id=period_id, 
        thisItem.term_of_payment_id=term_of_payment_id,
        thisItem.detail=detail
        # thisItem.start_at=start,
        # thisItem.end_at=end,
    
    db.session.commit()
    
    
    term_years = request.form.getlist('term_year[]')
    print(term_years)
    print(f"price_2025: {request.form.get('price_2025')}")
   


    
    for year in term_years:
        ids = request.form.getlist(f'term_id_{year}[]')
        amounts = request.form.getlist(f'installments_{year}[]')
        details = request.form.getlist(f'term_detail_{year}[]')
        check_vats_raw = request.form.getlist(f'check_vat_{year}[]')  # ได้ list string เช่น ['0', 'on', '0', 'on', ...]

        print("check_vats_raw:", check_vats_raw)

        price_str = request.form.get(f'price_{year}', '0').replace(',', '')
        price = Decimal(price_str or '0')

        check_vats = []
        i = 0
        while i < len(check_vats_raw):
            val = check_vats_raw[i]
            if val == '0':
                # ถ้า next คือ 'on' หรือ '1' → ติ๊ก
                if i + 1 < len(check_vats_raw) and check_vats_raw[i + 1] in ['on', '1']:
                    check_vats.append(True)
                    i += 2  # ข้าม 2 ตัว
                else:
                    check_vats.append(False)
                    i += 1
            else:
                # fallback กรณีไม่ตรง pattern
                i += 1

        print(check_vats)

        existing_ids_in_db = [
            str(x.id) for x in installmentsPaymentModel.query.filter_by(
                year=year,
                product_for_sales_id=thisItem.id
            ).all()
        ]

        # 🟩 หา id ที่หายไป
        ids_from_form = [id.strip() for id in ids if id.strip()]
        ids_to_delete = set(existing_ids_in_db) - set(ids_from_form)

        # 🔥 ลบรายการที่ไม่มีในฟอร์มแล้ว
        if ids_to_delete:
            installmentsPaymentModel.query.filter(
                installmentsPaymentModel.id.in_(ids_to_delete)
            ).delete(synchronize_session=False)

        for i in range(len(amounts)):
            amount = Decimal(amounts[i].replace(',', ''))
            detail = details[i].strip()
            term_id = ids[i].strip() if i < len(ids) else None
            # check_vat = check_vats[i] if i < len(check_vats) else False  # fallback ถ้าข้อมูลไม่ครบ
            # check_vat ให้เช็คว่ามีข้อมูลใน check_vats หรือเปล่า
            if check_vats_raw:
                check_vat = check_vats[i] if i < len(check_vats) else False
            else:
                check_vat = None  # หรือจะใช้ None เพื่อบอกว่าไม่เปลี่ยนค่า

            if term_id:
                existing = installmentsPaymentModel.query.filter_by(id=term_id).first()
                if existing:
                    existing.term_detail = detail
                    existing.amount = amount
                    existing.year = year
                    existing.price = price
                    if check_vat is not None:
                        existing.check_vat = check_vat
                    continue

        
            db.session.add(installmentsPaymentModel(
                term_detail=detail,
                amount=amount,
                year=year,
                price=price,
                product_for_sales_id=thisItem.id,
                check_vat=check_vat if check_vat is not None else False,
            ))

    db.session.commit()
    # installments_list = request.form.getlist('installments')  
    # term_detail_list = request.form.getlist('term_detail') 
    # term_id_list = request.form.getlist('term_id')
    # term_year_list = request.form.getlist('term_year')  # 🟩 ดึงปีมาด้วย


    # db.session.query(installmentsPaymentModel).filter(
    # installmentsPaymentModel.product_for_sales_id == thisItem.id).delete()
    # db.session.commit()

    # # ตรวจสอบและบันทึก
    # if term_detail_list and installments_list and len(term_detail_list) == len(installments_list):
    #     for i in range(len(installments_list)):
    #         term = term_detail_list[i].strip()
    #         amount = installments_list[i].strip().replace(',', '')
    #         year = term_year_list[i].strip() if i < len(term_year_list) else None

    #         if term_id_list and i < len(term_id_list) and term_id_list[i].strip():
    #             term_id = term_id_list[i].strip()
    #             existing_item = installmentsPaymentModel.query.filter_by(id=term_id).first()
    #             if existing_item:
    #                 existing_item.term_detail = term
    #                 existing_item.amount = amount
    #                 existing_item.year = year
    #             else:
    #                 db.session.add(installmentsPaymentModel(
    #                     term_detail=term,
    #                     amount=amount,
    #                     year=year,
    #                     product_for_sales_id=thisItem.id
    #                 ))
    #         else:
    #             db.session.add(installmentsPaymentModel(
    #                 term_detail=term,
    #                 amount=amount,
    #                 year=year,
    #                 product_for_sales_id=thisItem.id
    #             ))

    #     db.session.commit()
    #     print("All data saved successfully!")  # แจ้งเตือนว่าเซฟสำเร็จ
    # else:
    #     print("Error: term_detail_list and installments_list do not match in length.")

    
   
    if request.files:
        uploaded_images = request.files.getlist("formFile_img")
        uploaded_files = request.files.getlist("formFile_file")

        # ✅ ตรวจสอบว่ามีการอัปโหลดรูปภาพใหม่หรือไม่
        if any(img.filename for img in uploaded_images):  
            # 🔹 ลบรูปภาพเดิมก่อน
            old_images = MD_Image.query.filter_by(product_for_sales_id=thisItem.id).all()
            image_directory = os.path.join("apps", "static", "assets", "img", "product")
            os.makedirs(image_directory, exist_ok=True)  

            for old_image in old_images:
                old_file_path = os.path.join(image_directory, old_image.image)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)  # ลบไฟล์รูปเดิมออกจากโฟลเดอร์

            # ลบข้อมูลรูปภาพเดิมออกจากฐานข้อมูล
            MD_Image.query.filter_by(product_for_sales_id=thisItem.id).delete()
            db.session.commit()

            # ✅ เพิ่มรูปภาพใหม่เข้าไป
            for img in uploaded_images:
                if img.filename:
                    filename = f"{uuid.uuid4().hex}.{img.filename.split('.')[-1]}"
                    file_path = os.path.join(image_directory, filename)
                    img.save(file_path)

                    new_image = MD_Image(image=filename, product_for_sales_id=thisItem.id)
                    db.session.add(new_image)

            db.session.commit()

        # ✅ ตรวจสอบว่ามีการอัปโหลดไฟล์เอกสารใหม่หรือไม่
        if  uploaded_files:
            count = 0
            if request.files.getlist("formFile_file"):
                for i, file_qu in enumerate(request.files.getlist("formFile_file")):
                    if file_qu.filename == '':
                        break
                    target = 'apps/static/assets/files/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_qu.filename.split('.')
                    id_order = thisItem.id
                    filename = f'{id_order}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    # print(file_path)
                    try:
                        file_qu.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileModel(filename=filename,filepath=file_path,file_type =1, product_for_sales_id=thisItem.id)
                    db.session.add(newfile)

            db.session.commit()
    
    db.session.query(ProductSupplierAssociation).filter(ProductSupplierAssociation.product_id == thisItem.id).delete()
    db.session.query(ProductEmployerAssociation).filter(ProductEmployerAssociation.product_id == thisItem.id).delete()
    db.session.query(ProductOrganizationAssociation).filter(ProductOrganizationAssociation.product_id == thisItem.id).delete()
    db.session.commit()    
        
    if organization_ids:
        for organization_id in organization_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_association = ProductOrganizationAssociation(
                product_id=thisItem.id,
                organization_id=organization_id,
            )

            db.session.add(new_association)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Organization เข้าโครงการสำเร็จ")
    
        
    if employee_ids:
        for employee_ids in employee_ids:
            # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
            new_associationEmployee = ProductEmployerAssociation(
                product_id=thisItem.id,
                employee_id=employee_ids,
            )

            db.session.add(new_associationEmployee)

        db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
        print("เพิ่ม Employee เข้าโครงการสำเร็จ")  
    # 🔴 ลบความสัมพันธ์เดิมทั้งหมดก่อน
    ProductAgencyAssociation.query.filter_by(product_id=thisItem.id).delete()

    # 🟢 รวม id ทั้งสองกลุ่ม
    all_agency_ids = set((university_ids or []) + (agency_ids or []))

    # 🟢 เพิ่มใหม่
    for agency_id in all_agency_ids:
        new_association = ProductAgencyAssociation(
            product_id=thisItem.id,
            agency_id=agency_id,
        )
        db.session.add(new_association)

    db.session.commit()  # ✅ commit รอบเดียว
    print("อัปเดต university และ agency เข้าโครงการสำเร็จ")
    # ProductAgencyAssociation.query.filter_by(product_id=thisItem.id).delete()

    # if university_ids:
    #     for university_id in university_ids:
    #         # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
    #         new_associationAgency = ProductAgencyAssociation(
    #             product_id=thisItem.id,
    #             agency_id=university_id,
    #         )

    #         db.session.add(new_associationAgency)

    #     db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
    #     print("เพิ่ม university  เข้าโครงการสำเร็จ")   
        
    # if agency_ids:
    #     for agency_id in agency_ids:
    #         # สร้างความสัมพันธ์ในตาราง ProgramSupplierAssociation
    #         new_associationAgency = ProductAgencyAssociation(
    #             product_id=thisItem.id,
    #             agency_id=agency_id,
    #         )

    #         db.session.add(new_associationAgency)

    #     db.session.commit()  # บันทึกข้อมูลลงฐานข้อมูล
    #     print("เพิ่ม Agency เข้าโครงการสำเร็จ")   
    # # print(datas)
    return redirect(url_for('product_blueprint.EditProductSales',id=thisItem.id))

@blueprint.route('/upload')
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file.save(f"./uploads/{file.filename}")
    return jsonify({"message": "Upload successful!"})


@blueprint.route('/download/<filename>')
def downloadFile(filename):
    
    file = FileModel.query.filter_by(filename=filename).first()
   
    filename_without_ext, file_extension = file.filepath.rsplit('.', 1)

    # print(f"ชื่อไฟล์: {filename_without_ext}")  
    # print(f"นามสกุล: {file_extension}")  # pd
    path = "static\\assets\\files\\" + file.filename+'.'+file_extension   
    file_path = os.path.join(path)    # file = FileModel.query.filter_by(filename=filename).first()
    
   

    

    
    return send_file(file_path, as_attachment=True)


@blueprint.route('/product_delete_file', methods=['POST'])
@login_required
def product_delete_file():  
    # print(request.form)
    id_file = request.form["id_file"]
    id_product = request.form["id_product"]
    thisFile= FileModel.query.filter_by(id=id_file).first()
    
    
    if thisFile.file_type == 1:
        try:
            
            path = "apps\\static\\assets\\files\\" + thisFile.filename+'.pdf'
            file_path = os.path.join(path)
            # print(file_path)
            os.remove(file_path)
        except FileNotFoundError:
            print(f"ไม่พบไฟล์: {file_path}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        # thisFile.flag_delete = True
        db.session.query(FileModel).filter(FileModel.id == id_file).delete()
        db.session.commit()
        

    return redirect(url_for('product_blueprint.productSales', id=id_product))

@blueprint.route('/delete_img', methods=['POST'])
@login_required
def delete_img():
    id_img = request.form["id"]

    thisImage = MD_Image.query.filter_by(id=id_img).first()

    if not thisImage:  # เช็กว่าเจอรูปหรือไม่
        print(f"ไม่พบรูปภาพที่มี ID: {id_img}")
        return redirect(url_for('product_blueprint.EditProductSales', id=0))  # หรือไปหน้าอื่นที่เหมาะสม

    try:
        path = os.path.join("apps", "static", "assets", "img", "product", thisImage.filename)
        os.remove(path)
    except FileNotFoundError:
        print(f"ไม่พบไฟล์: {path}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")

    product_id = thisImage.product_for_sales_id  # ✅ เก็บค่าไว้ก่อนลบ

    db.session.delete(thisImage)
    db.session.commit()

    return redirect(url_for('product_blueprint.EditProductSales', id=product_id))


@blueprint.route('/save_payment', methods=['POST'])
def save_payment():
    data = request.get_json()
    year = data.get('year')
    price = data.get('price')
    term = data.get('term')
    product_id = data.get('product_id')
    terms = data.get('terms', [])

    try:
        # อัปเดตราคาขายของสินค้าหลัก
        product = ProductForSalesModel.query.get(product_id)
        if product:
            product.price = price
            product.term_of_payment_id = term

        # ลูป terms แล้วอัปเดต/เพิ่ม
        for t in terms:
            term_id = t.get('id')
            detail = t.get('detail')
            amount = t.get('amount')

            if term_id:  # ถ้ามี id ให้แก้ไข
                inst = installmentsPaymentModel.query.get(term_id)
                if inst:
                    inst.term_detail = detail
                    inst.amount = amount
            else:  # ถ้ายังไม่มี ให้เพิ่มใหม่
                new_payment = installmentsPaymentModel(
                    product_for_sales_id=product_id,
                    year=year,
                    term_detail=detail,
                    amount=amount
                )
                db.session.add(new_payment)

        db.session.commit()
        return jsonify({"status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})



