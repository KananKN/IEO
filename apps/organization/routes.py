
import time
import re
from apps.organization import blueprint
from apps.authentication.models import *
from apps.organization.models import *
from apps.product.models import *
from apps.supplier.models import *
from apps.employee.models import *
from apps.coordinator.models import *
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

read_permission = Permission(RoleNeed("read_organization"))
write_permission = Permission(RoleNeed("write_organization"))
delete_permission = Permission(RoleNeed("delete_organization"))


# ---------- Fees ------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def organization():
    datas = EmployeeModel.query.all()
    # print(datas)
    return render_template('organization/organization.html', segment='organization' ,datas=datas, )

@blueprint.route("/get_organization", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_organization():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: OrganizationModel.id,          # คอลัมน์ที่ 0 -> id
        1: OrganizationModel.name,        # คอลัมน์ที่ 1 -> name
        2: OrganizationModel.country_id,  # คอลัมน์ที่ 2 -> description
        3: OrganizationModel.tel # คอลัมน์ที่ 2 -> description
    }

    # จัดเรียงลำดับข้อมูล
    if order:
        column_index = int(order[0]["column"])  # ดึง index ของคอลัมน์ที่ต้องการเรียง
        column_order = column_map.get(column_index, OrganizationModel.id)  # คอลัมน์ที่ใช้เรียง
        sort_direction = order[0]["dir"]  # asc / desc

        if sort_direction == "desc":
            column_order = column_order.desc()
    else:
        column_order = OrganizationModel.id.asc()  # เรียงตาม ID ถ้าไม่มี order

    # ค้นหาข้อมูล
    search = f"%{search_value}%"

    query = db.session.query(OrganizationModel).\
        outerjoin(CountryModel, CountryModel.id == OrganizationModel.country_id).\
        filter(
            or_(
                OrganizationModel.name.ilike(search),
                CountryModel.name.ilike(search),
                OrganizationModel.tel.ilike(search)
            )
        )

    # นับจำนวนแถวทั้งหมด
    total_records = query.count()

    # ดึงข้อมูลตามลำดับและช่วงที่กำหนด
    organizations = query.order_by(column_order).offset(start).limit(length).all()
    # แปลงข้อมูลเป็น JSON
    data = [{
        "id": index + 1,
        "data_id": organization.id,
        "name": organization.name,
        "country": organization.country.name,
        "tel": organization.tel,
        
    } for index, organization in enumerate(organizations)]

    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": total_records,
        "data": data
    })

    
@blueprint.route('/organization_create')
@login_required
@read_permission.require(http_exception=403)
def organization_create():
    datas = OrganizationModel.query.all()
    countrylist = CountryModel.query.all()
    return render_template('organization/organization_create.html', segment='organization' ,datas=datas,countrylist=countrylist,)   

@blueprint.route('/createOrganization', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def createOrganization():
    print(request.form)
    
    try:
        name_company =request.form.get('n_nameCompany')
        tax =request.form.get('n_tax')
        country =request.form.get('n_country')
        address =request.form.get('address')
        name_coondinator =request.form.get('name_coondinator')
        email =request.form.get('email')
        tel =request.form.get('tel')
        
        bank = request.form.get('n_bank')
        account_number = request.form.get('n_accountNumber')
        bank_branch = request.form.get('n_bankBranch')
        type_bank = request.form.get('account_type')
        foreign_banks = request.form.get('foreign_banks')
        swiftCode = request.form.get('n_swiftCode')
        bank_address = request.form.get('n_bank_address')
        note = request.form.get('n_note')
        account_name = request.form.get('n_accountName')
        foreign_banks_name = request.form.get('foreign_banks_name')

        # ดึงข้อมูลลิสต์จากฟอร์ม
        name_coordinators_list = request.form.getlist('name_coordinator')
        coordinatorTell_list = request.form.getlist('name_coordinatorTell')
        coordinatorEmail_list = request.form.getlist('name_coordinatorEmail')
        
        
        existing_organization_by_name = OrganizationModel.query.filter_by(name=name_company).first()
        if existing_organization_by_name:
            flash("ชื่อบริษัทซ้ำ: " + existing_organization_by_name.name, "warning")
            return redirect(url_for('organization_blueprint.organization_create'))

        existing_organization_by_tax = OrganizationModel.query.filter_by(tax=tax).first()
        if existing_organization_by_tax:
            flash("เลขผู้เสียภาษีซ้ำ: " + existing_organization_by_tax.tax, "warning")
            return redirect(url_for('organization_blueprint.organization_create'))
        
        # if name_check:
        #     flash("ไม่สามารถบันทึกข้อมูลได้", "danger")
        else :
            newItem = OrganizationModel(name=name_company,
                                    tax=tax,
                                    address=address,
                                    tel=tel,
                                    email=email,
                                    country_id=country,
                                    name_coondinator=name_coondinator,
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
            db.session.add(newItem)
            db.session.commit()
            
            if len(name_coordinators_list) > 0:
                # ตรวจสอบว่าลิสต์มีขนาดเท่ากัน
                print("coordinatorTell_list")
                if len(name_coordinators_list) == len(coordinatorTell_list) == len(coordinatorEmail_list):
                    for name_coordinator, coordinatorTell, coordinatorEmail in zip(
                        name_coordinators_list, coordinatorTell_list, coordinatorEmail_list
                    ):
                        
                        print(name_coordinators_list)
                        print(coordinatorTell_list)
                        print(coordinatorEmail_list)
                        order_item = CoordinatorModel(
                            organization_id=newItem.id,
                            name=name_coordinator,
                            tel=coordinatorTell,
                            email=coordinatorEmail,
                            
                        )
                        db.session.add(order_item)
                    db.session.commit()
                else:
                    flash("Error: Coordinator lists have mismatched lengths!", "danger")
                    return redirect(url_for('organization_blueprint.organization'))
            flash("Add success!", "success")
            
        if  request.files:
            count = 0
            if request.files.getlist("formFile"):
                for i, file_PO in enumerate(request.files.getlist("formFile")):
                    if file_PO.filename == '':
                        break
                    target = 'apps/static/assets/files/organization/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    organization_id = newItem.id
                    filename = f'{organization_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileOrganizationModel(filename=file_name,filepath=file_path,file_type =1, organization_id=newItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('organization_blueprint.organization'))
    
    

 
    
@blueprint.route('/organization_update/<id>')
@login_required
@read_permission.require(http_exception=403)
def organization_update(id):
    datas = OrganizationModel.query.filter_by(id=id).first()
    countrylist = CountryModel.query.all()
    countrylist = CountryModel.query.all()
    coordinators = CoordinatorModel.query.filter_by(organization_id  = datas.id).all()
    file_data = FileOrganizationModel.query.filter_by(organization_id  = datas.id).all()
    return render_template('organization/organization_update.html', segment='organization' ,datas=datas,countrylist=countrylist,file_data=file_data,coordinators=coordinators)    


@blueprint.route('/downloadOrganization/<filename>')
def downloadOrganization(filename):
    
    file = FileOrganizationModel.query.filter_by(filename=filename).first()
   
    filename_without_ext, file_extension = file.filepath.rsplit('.', 1)

    path = "static\\assets\\files\\organization\\" + file.filename   
    file_path = os.path.join(path)    # file = FileModel.query.filter_by(filename=filename).first()
    
    
    return send_file(file_path, as_attachment=True)

@blueprint.route('/organization_delete_file', methods=['POST'])
@login_required
def organization_delete_file():  
    # print(request.form)
    id_file = request.form["id_file"]
    id_organization = request.form["id"]
    thisFile= FileOrganizationModel.query.filter_by(id=id_file).first()
    
    
    if thisFile.file_type == 1:
        try:
            
            path = "apps\\static\\assets\\files\\organization\\" + thisFile.filename
            file_path = os.path.join(path)
            # print(file_path)
            os.remove(file_path)
        except FileNotFoundError:
            print(f"ไม่พบไฟล์: {file_path}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        # thisFile.flag_delete = True
        db.session.query(FileOrganizationModel).filter(FileOrganizationModel.id == id_file).delete()
        db.session.commit()
        

    return redirect(url_for('organization_blueprint.organization_update', id=id_organization))

@blueprint.route('/updateOrganization', methods=['POST'])
@login_required
@read_permission.require(http_exception=403)
def updateOrganization():
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
        
        
        type_bank = request.form.get('account_type')
        bank = request.form.get('n_bank')
        account_number = request.form.get('n_accountNumber')
        bank_branch = request.form.get('n_bankBranch')
        type_bank = request.form.get('account_type')
        foreign_banks = request.form.get('foreign_banks')
        swiftCode = request.form.get('n_swiftCode')
        bank_address = request.form.get('n_bank_address')
        note = request.form.get('n_note')
        account_name = request.form.get('n_accountName')
        foreign_banks_name = request.form.get('foreign_banks_name')    
        
        name_coordinators_list = request.form.getlist('name_coordinator')
        coordinatorTell_list = request.form.getlist('name_coordinatorTell')
        coordinatorEmail_list = request.form.getlist('name_coordinatorEmail')
        thisItem = OrganizationModel.query.filter_by(id=id).first()
        
        if thisItem:
            
            if name_company != thisItem.name:
                name_check = OrganizationModel.query.filter_by(name=name_company).first()
                if name_check:
                    flash("ไม่สามารถบันทึกข้อมูลได้: ชื่อซ้ำกับในระบบ", "danger")
                    return redirect(url_for('organization_blueprint.organization'))
                
            thisItem.name=name_company
            thisItem.tax=tax
            thisItem.country_id=country
            thisItem.address=address  
            thisItem.name_coondinator=name_coondinator 
            thisItem.email=email
            thisItem.tel=tel
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
            db.session.commit()
            
            db.session.query(CoordinatorModel).filter(CoordinatorModel.organization_id == id).delete()
            db.session.commit()
            if len(name_coordinators_list) > 0:
                # ตรวจสอบว่าลิสต์มีขนาดเท่ากัน
                print("coordinatorTell_list")
                if len(name_coordinators_list) == len(coordinatorTell_list) == len(coordinatorEmail_list):
                    for name_coordinator, coordinatorTell, coordinatorEmail in zip(
                        name_coordinators_list, coordinatorTell_list, coordinatorEmail_list
                    ):
                        
                        print(name_coordinators_list)
                        print(coordinatorTell_list)
                        print(coordinatorEmail_list)
                        order_item = CoordinatorModel(
                            organization_id=thisItem.id,
                            name=name_coordinator,
                            tel=coordinatorTell,
                            email=coordinatorEmail,
                            
                        )
                        db.session.add(order_item)
                    db.session.commit()
                else:
                    flash("Error: Coordinator lists have mismatched lengths!", "danger")
                    return redirect(url_for('organization_blueprint.organization_update'))
            flash("Update success!", "success")
        
            
        if  request.files:
            count = 0
            if request.files.getlist("formFile"):
                for i, file_PO in enumerate(request.files.getlist("formFile")):
                    if file_PO.filename == '':
                        break
                    target = 'apps/static/assets/files/organization/'
                    os.makedirs(target, exist_ok=True)  # สร้างโฟลเดอร์หากยังไม่มีอยู่
                    ftype = file_PO.filename.split('.')
                    organization_id = thisItem.id
                    filename = f'{organization_id}_{ftype[0]}_{i}'
                    file_name = filename + '.' + ftype[-1]

                    file_path = os.path.join(target, file_name)
                    try:
                        file_PO.save(file_path)  # บันทึกไฟล์
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500  # ส่งกลับหากมีข้อผิดพลาด
                    count += 1
                    newfile = FileOrganizationModel(filename=file_name,filepath=file_path,file_type =1, organization_id=thisItem.id)
                    db.session.add(newfile)
                    db.session.commit()    
    except Exception as e:
        # จับข้อผิดพลาดและแสดงข้อความ
        # flash(f"An error occurred: {str(e)}", "danger")
        print(f"[ERROR] {e}")   
        flash("ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่", "danger")
        # logging.error(f"เกิดข้อผิดพลาด: {e}", exc_info=True)
        db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด

    return redirect(url_for('organization_blueprint.organization_update', id=id))


@blueprint.route('/delete_organization', methods=['POST'])
@login_required
def delete_organization():
    id_del = request.form["id"]

    file_list = FileOrganizationModel.query.filter_by(organization_id=id_del).all()

    for file_item in file_list:
        if file_item.file_type == 1:
            try:
                file_path = os.path.join("apps", "static", "assets", "files", "organization", file_item.filename)
                os.remove(file_path)
            except FileNotFoundError:
                print(f"❌ ไม่พบไฟล์: {file_path}")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
    # thisFile.flag_delete = True
    ProductOrganizationAssociation.query.filter_by(organization_id=id_del).delete()
    db.session.query(OrganizationModel).filter(OrganizationModel.id == id_del).delete()
    db.session.query(FileOrganizationModel).filter(FileOrganizationModel.organization_id == id_del).delete()
    db.session.commit()
        
    flash(' Deleted!', 'success')
    return redirect(url_for('organization_blueprint.organization'))


@blueprint.route('/list_Productorganization')
@login_required
@read_permission.require(http_exception=403)
def list_Productorganization():
    datas = OrganizationModel.query.all()
    for organization in datas:
        product_organization = ProductOrganizationAssociation.query.filter_by(organization_id=organization.id).first()
    print(datas)
    # print(datas)
    return render_template('organization/list_ProductOrganization.html', segment='list_Productorganization' ,datas=datas, )

@blueprint.route("/get_listProductorganization", methods=["POST"])
@login_required
@read_permission.require(http_exception=403)
def get_listProductorganization():
    request_data = request.get_json()
    draw = request_data.get("draw", 1)
    start = request_data.get("start", 0)
    length = request_data.get("length", 10)
    order = request_data.get("order", [])
    search_value = request_data.get("search", {}).get("value", "")

    Product = aliased(ProductForSalesModel)
    Organization = aliased(OrganizationModel)
    
    # Mapping คอลัมน์จาก DataTable ไปยัง Database
    column_map = {
        0: Organization.id,          # คอลัมน์ที่ 0 -> id
        1: Organization.name,        # คอลัมน์ที่ 1 -> name
        2: Organization.country_id,  # คอลัมน์ที่ 2 -> description
        3: Organization.tel,         # คอลัมน์ที่ 3 -> tel
        4: Product.name          # คอลัมน์ที่ 4 -> product
    }
   
    base_query = db.session.query(Organization.id).\
        outerjoin(CountryModel).\
        outerjoin(ProductOrganizationAssociation, Organization.id == ProductOrganizationAssociation.organization_id).\
        outerjoin(Product, Product.id == ProductOrganizationAssociation.product_id)

    if search_value:
        search = f"%{search_value}%"
        base_query = base_query.filter(
            or_(
                Organization.name.ilike(search),
                Organization.tel.ilike(search),
                CountryModel.name.ilike(search),
                Product.name.ilike(search)
            )
        )

    base_query = base_query.distinct()  # กันซ้ำ
    # Pagination
    total_records = db.session.query(Organization.id).distinct().count()
    filtered_records = base_query.count()

    # Step 2: paginate ที่ระดับ organization
    organization_ids = base_query.offset(start).limit(length).all()
    organization_ids = [e.id for e in organization_ids]
    
    query = db.session.query(Organization, Product.name).\
        filter(Organization.id.in_(organization_ids)).\
        outerjoin(ProductOrganizationAssociation, Organization.id == ProductOrganizationAssociation.organization_id).\
        outerjoin(Product, Product.id == ProductOrganizationAssociation.product_id).\
        outerjoin(CountryModel, CountryModel.id == Organization.country_id).\
        order_by(Organization.id)

    rows = query.all()
    # Group ข้อมูลตาม employee_id
    grouped = {}
    display_index = start + 1  # 👈 เริ่มนับลำดับที่ 1


    for organization, product_name in rows:
        organization_id = organization.id

        if organization_id not in grouped:
            grouped[organization_id] = {
                "id": display_index ,
                "data_id": organization.id,
                "name": organization.name,
                "country": organization.country.name if organization.country else "-",
                "tel": organization.tel,
                "product": set()
            }
            display_index += 1 
        if product_name:
            grouped[organization_id]["product"].add(product_name)

    # แปลง set → string และแสดงผลเป็น badge
    data = []
    for organization in grouped.values():
        if organization["product"]:
            badges = list(sorted(organization["product"]))
            badge_html = ""
            for i, p in enumerate(badges):
                comma = "," if i < len(badges) - 1 else ""
                badge_html += f'<span class="badge bg-info text-white mb-1">{p.strip()}</span>{comma}'
            
            organization["product"] = f'<div class="product-badges">{badge_html}</div>'
        else:
            organization["product"] = "ไม่มีโครงการ"
        # สร้าง badge สำหรับแต่ละ product
        data.append(organization)

    # ส่งออกข้อมูล
    return jsonify({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": filtered_records,
        "data": data
    })     