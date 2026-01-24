
import time
import re
from apps.account import blueprint
from apps.authentication.models import *
from apps.product.models import *
from apps.supplier.models import *
from apps.account.models import *
from apps.lead.models import *
from apps.order.models import *
from apps.employee.models import *
from apps.coordinator.models import *
from apps.organization.models import *

from apps import db
from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort, send_file, current_app
from flask_login import login_required, current_user, logout_user
from jinja2 import TemplateNotFound
import random
import string
import requests
import base64
from io import BytesIO
from PIL import Image
from flask_principal import Permission, RoleNeed
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime
import uuid
from sqlalchemy import and_, func, case, asc, or_, cast, Integer
from sqlalchemy.orm import aliased
from collections import defaultdict
from sqlalchemy.dialects import postgresql
import traceback

from decimal import Decimal, InvalidOperation


UPLOAD_FOLDER = 'uploads/expense'

read_permission = Permission(RoleNeed("read_account"))
write_permission = Permission(RoleNeed("write_account"))
delete_permission = Permission(RoleNeed("delete_account"))

@blueprint.route('/expense_categories')
@login_required
@read_permission.require(http_exception=403)
def expense_categories():
    datas = ExpenseCategoryModel.query.all()
    print(datas)
    datas_dict = [d.to_dict() for d in datas]

    # return jsonify([
    #     d.to_dict() for d in datas
    # ])
    return render_template('expense/expense_categories.html', segment='expense_categories' ,datas=datas,datas_json=datas_dict)

def model_to_dict(model):
    data = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        if isinstance(value, bytes):  # ตรวจสอบว่าเป็น bytes หรือไม่
            # แปลงเป็น base64 หรือ string
            value = base64.b64encode(value).decode('utf-8')
        data[c.name] = value
    return data

@blueprint.route('/add_expense', methods=['POST'])
@login_required 
@write_permission.require(http_exception=403)
def add_expense():
    data = request.get_json()
    print(data)
    try:
        new_expense = ExpenseCategoryModel(
            name=data['name'],
            # description=data.get('description', ''),
            # parent_id=data.get('parent_id', None),
            # is_active=True
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Expense category added successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@blueprint.route('/edit_expense', methods=['POST'])
@login_required
@write_permission.require(http_exception=403)
def edit_expense():
    data = request.get_json()
    print(data)
    try:
        expense = ExpenseCategoryModel.query.get(data['id'])
        if not expense:
            return jsonify({'status': 'error', 'message': 'Expense category not found.'}), 404

        expense.name = data['name']
        # expense.description = data.get('description', expense.description)
        # expense.parent_id = data.get('parent_id', expense.parent_id)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Expense category updated successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@blueprint.route('/delete_expense/<int:expense_id>', methods=['DELETE'])
@login_required
@delete_permission.require(http_exception=403)
def delete_expense(expense_id):
    try:
        expense = ExpenseCategoryModel.query.get(expense_id)
        if not expense:
            return jsonify({
                'status': 'error',
                'message': 'Expense category not found'
            }), 404

        db.session.delete(expense)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Expense category deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blueprint.route('/subcategory/<int:category_id>')
@login_required
@read_permission.require(http_exception=403)
def subcategory(category_id):
    data_cat = ExpenseCategoryModel.query.filter_by(id=category_id).first()
    data_sub = ExpenseSubCategoryModel.query.filter_by(expense_category_id=category_id).all()
    
    datas_dict = [d.to_dict() for d in data_sub]

    print(datas_dict)
    # return jsonify([
    #     d.to_dict() for d in datas
    # ])
    return render_template('expense/subcategorie.html', segment='expense_categories' ,data_sub=data_sub,datas_json=datas_dict,data_cat=data_cat)

    
@blueprint.route('/add_subexpense', methods=['POST'])
@login_required 
@write_permission.require(http_exception=403)   
def add_subexpense():
    data = request.get_json()
    print(data)
    try:
        new_expense = ExpenseSubCategoryModel(
            expense_category_id=data['id_cat'],
            name=data['name'],
            # description=data.get('description', ''),
            # parent_id=data.get('parent_id', None),
            # is_active=True
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sub expense item added successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@blueprint.route('/edit_subexpense', methods=['POST'])
@login_required
@write_permission.require(http_exception=403)
def edit_subexpense():
    data = request.get_json()
    print(data)
    try:
        expense_sub = ExpenseSubCategoryModel.query.get(data['id'])
        if not expense_sub:
            return jsonify({'status': 'error', 'message': 'expense_sub category not found.'}), 404

        expense_sub.name = data['name']
        # expense.description = data.get('description', expense.description)
        # expense.parent_id = data.get('parent_id', expense.parent_id)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Expense subcategory updated successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@blueprint.route('/delete_subexpense/<int:expense_id>', methods=['DELETE'])
@login_required
@delete_permission.require(http_exception=403)
def delete_subexpense(expense_id):
    try:
        expense_sub = ExpenseSubCategoryModel.query.get(expense_id)
        if not expense_sub:
            return jsonify({
                'status': 'error',
                'message': 'Expense subcategory not found'
            }), 404

        db.session.delete(expense_sub)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Expense subcategory deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blueprint.route('/currencies')
@login_required
@read_permission.require(http_exception=403)
def currencies():
    data = CurrencyModel.query.all()
    
    datas_dict = [d.to_dict() for d in data]

    print(data)
    # return jsonify([
    #     d.to_dict() for d in datas
    # ])
    return render_template('expense/currencies.html', segment='currencies' ,datas=data,datas_json=datas_dict)


@blueprint.route('/add_currencies', methods=['POST'])
@login_required
@write_permission.require(http_exception=403)
def add_currencies():
    data = request.get_json()
    print(data)

    try:
        name = data.get('name')
        code = data.get('code')

        # 1️⃣ validate required fields
        if not name or not code:
            return jsonify({
                'status': 'error',
                'message': 'Currency name and code are required.'
            }), 400

        code = code.upper().strip()

        # 2️⃣ check duplicate code
        exists = CurrencyModel.query.filter_by(code=code).first()
        if exists:
            return jsonify({
                'status': 'error',
                'message': 'Currency code already exists.'
            }), 400

        # 3️⃣ create
        new_currency = CurrencyModel(
            name=name.strip(),
            code=code
        )

        db.session.add(new_currency)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Currency added successfully.'
        })

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@blueprint.route('/edit_currencies', methods=['POST'])
@login_required
@write_permission.require(http_exception=403)
def edit_currencies():
    data = request.get_json()
    print(data)

    try:
        currency = CurrencyModel.query.get(data.get('id'))
        if not currency:
            return jsonify({
                'status': 'error',
                'message': 'Currency not found.'
            }), 404

        # 🔎 validate
        name = data.get('name', '').strip()
        code = data.get('code', '').strip().upper()

        if not name or not code:
            return jsonify({
                'status': 'error',
                'message': 'Name and code are required.'
            }), 400

        # 🔁 check duplicate (name OR code) except self
        duplicate = CurrencyModel.query.filter(
            CurrencyModel.id != currency.id,
            db.or_(
                CurrencyModel.code == code,
                CurrencyModel.name == name
            )
        ).first()

        if duplicate:
            return jsonify({
                'status': 'error',
                'message': 'Currency name or code already exists.'
            }), 400

        # ✅ update
        currency.name = name
        currency.code = code

        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Currency updated successfully.'
        })

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@blueprint.route('/delete_currencies/<int:currency_id>', methods=['DELETE'])
@login_required
@delete_permission.require(http_exception=403)
def delete_currencies(currency_id):
    print(currency_id)
    try:
        currency = CurrencyModel.query.get(currency_id)
        if not currency:
            return jsonify({
                'status': 'error',
                'message': 'Currency not found.'
            }), 404

        # 🔒 ถ้ามีการใช้งานอยู่ (ตัวอย่าง)
        # used = ExpenseModel.query.filter_by(currency_id=currency_id).first()
        # if used:
        #     return jsonify({
        #         'status': 'error',
        #         'message': 'ไม่สามารถลบได้ เนื่องจากมีการใช้งานสกุลเงินนี้แล้ว'
        #     }), 400

        db.session.delete(currency)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Currency deleted successfully.'
        })

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@blueprint.route('/expense_claims_list')
@login_required 
@read_permission.require(http_exception=403)
def expense_claims_list():  
    data = ExpenseClaim.query.all()
    
    datas_dict = [d.to_dict() for d in data]
    
    # return jsonify([
    #     d.to_dict() for d in datas
    # ])
    return render_template('expense/expense_claims_list.html', segment='expense_claims' ,datas=data,datas_json=datas_dict)

@blueprint.route('/expense_create_claims')
@login_required 
@read_permission.require(http_exception=403)
def expense_create_claims():  
    members = (MemberModel.query.join(MemberModel.orders)
    .distinct().order_by(MemberModel.first_name.asc())  # 🔤 เรียงตามชื่อ
    .all())

    users = UserModel.query.all()
    categories = ExpenseCategoryModel.query.all()
    currency = CurrencyModel.query.order_by(CurrencyModel.code.asc()).all()


    # datas_members_dict = [d.to_dict() for d in members]

    data_supplier = []

    employees = EmployeeModel.query.all()
    organizations = OrganizationModel.query.all()
    agencies = AgencyModel.query.filter(AgencyModel.org_type == 'agency').all()
    university = AgencyModel.query.filter(AgencyModel.org_type == 'university').all()
    suppliers = SupplierModel.query.all()

    for e in employees:
        data_supplier.append({
            "value": f"employee:{e.id}",
            "name": e.name,
            "type": "Employee"
        })

    for o in organizations:
        data_supplier.append({
            "value": f"organization:{o.id}",
            "name": o.name,
            "type": "Organization"
        })

    for a in agencies:
        data_supplier.append({
            "value": f"agency:{a.id}",
            "name": f"{a.first_name} {a.last_name}",
            "type": "Agency"
        })

    for u in university:
        data_supplier.append({
            "value": f"agency:{a.id}",
            "name": f"{a.first_name} {a.last_name}",
            "type": "University"
        })

    for s in suppliers:
        data_supplier.append({
            "value": f"supplier:{s.id}",
            "name": s.name,
            "type": "Supplier"
        })

    # 🔤 เรียงตัวอักษร
    data_supplier = sorted(data_supplier, key=lambda x: x["name"].lower())
    
    return render_template('expense/expense_create_claims.html', segment='expense_claims' ,members=members
                    , users=users, categories=categories, data_supplier=data_supplier, currency=currency)


def get_receiver_detail(receiver_type, receiver_id):

    if receiver_type == 'employee':
        e = EmployeeModel.query.get(receiver_id)
        if not e:
            return None
        return {
            "name": e.account_name,
            "bank_name": e.bank,
            "bank_account": e.account_number,
            "type": "Employee"
        }

    if receiver_type == 'supplier':
        s = SupplierModel.query.get(receiver_id)
        if not s:
            return None
        return {
            "name": s.account_name,
            "bank_name": s.bank,
            "bank_account": s.account_number,
            "type": "Supplier"
        }

    if receiver_type == 'organization':
        o = OrganizationModel.query.get(receiver_id)
        if not o:
            return None
        return {
            "name": o.account_name,
            "bank_name": o.bank,
            "bank_account": o.account_number,
            "type": "Organization"
        }

    if receiver_type == 'agency':
        a = AgencyModel.query.get(receiver_id)
        if not a:
            return None
        return {
            # "name": f"{a.first_name} {a.last_name}",
            "name": a.account_name,
            "bank_name": a.bank,
            "bank_account": a.account_number,
            "type": "Agency"
        }
    
    if receiver_type == 'university':
        a = AgencyModel.query.get(receiver_id)
        if not a:
            return None
        return {
            # "name": f"{a.first_name} {a.last_name}",
            "name": a.account_name,
            "bank_name": a.bank,
            "bank_account": a.account_number,
            "type": "University"
        }

    return None



@blueprint.route('/expense_upgrade_claims/<int:claim_id>')
@login_required 
@read_permission.require(http_exception=403)
def expense_upgrade_claims(claim_id):  
    members = (MemberModel.query.join(MemberModel.orders)
    .distinct().order_by(MemberModel.first_name.asc())  # 🔤 เรียงตามชื่อ
    .all())

    users = UserModel.query.all()
    categories = ExpenseCategoryModel.query.all()
    currency = CurrencyModel.query.order_by(CurrencyModel.code.asc()).all()

    

    # datas_members_dict = [d.to_dict() for d in members]

    data_supplier = []

    employees = EmployeeModel.query.all()
    organizations = OrganizationModel.query.all()
    agencies = AgencyModel.query.filter(AgencyModel.org_type == 'agency').all()
    university = AgencyModel.query.filter(AgencyModel.org_type == 'university').all()
    suppliers = SupplierModel.query.all()

    for e in employees:
        data_supplier.append({
            "value": f"employee:{e.id}",
            "name": e.name,
            "type": "Employee"
        })

    for o in organizations:
        data_supplier.append({
            "value": f"organization:{o.id}",
            "name": o.name,
            "type": "Organization"
        })

    for a in agencies:
        data_supplier.append({
            "value": f"agency:{a.id}",
            "name": f"{a.first_name} {a.last_name}",
            "type": "Agency"
        })

    for u in university:
        data_supplier.append({
            "value": f"agency:{a.id}",
            "name": f"{a.first_name} {a.last_name}",
            "type": "University"
        })

    for s in suppliers:
        data_supplier.append({
            "value": f"supplier:{s.id}",
            "name": s.name,
            "type": "Supplier"
        })

    # 🔤 เรียงตัวอักษร
    data_supplier = sorted(data_supplier, key=lambda x: x["name"].lower())

    #---- ดึงข้อมูลเดิม ----
    claim = ExpenseClaim.query.get(claim_id)
    receiver_detail = []
    children_files = []
    staff_files = []

    items = []

    # กรณี STAFF
    if claim.staff_claim:
        items = [
            {
                "id": i.id,
                "item_name": i.item_name,
                "amount": float(i.amount or 0)
            }
            for i in claim.staff_claim.expense_staff_items
        ]if claim.staff_claim and claim.staff_claim.expense_staff_items else []

        staff_files = ExpenseClaimFileModel.query.filter_by(
            claim_id=claim_id,
            claim_type='staff'
        ).all()
    # กรณี CHILDREN
    elif claim.children_claim:
        children_files = ExpenseClaimFileModel.query.filter_by(
            claim_id=claim_id,
            claim_type='children'
        ).all()
        items = [
                    {
                        "project_name": child.project.name,
                        "project_id": child.project_id,
                        "member_id": child.member_id,
                        "expense_date": child.expense_date,
                        "description": child.description,

                        "expense_items": [   # 👈 j อยู่ใน list นี้
                            {
                                "id": j.id,
                                "currency": j.currency_id,
                                "amount": float(j.amount or 0),
                                "receiver_id": j.receiver_id,
                                "receiver_type": j.receiver_type,
                                "ref_amount": j.ref_amount,
                                "exchange_rate": j.exchange_rate,
                                "remark": j.remark,
                                # "receiver_detail": get_receiver_detail(
                                #         j.receiver_type,
                                #         j.receiver_id
                                #     )
                            }
                            for j in child.expense_children_items
                        ]
                        
                    }
                    for child in claim.children_claim
                ]
        for child in claim.children_claim:
            for j in child.expense_children_items:

                detail = {
                    "receiver_type": j.receiver_type,
                    "receiver_id": j.receiver_id,
                    "name": None,
                    "bank_name": None,
                    "bank_account": None,
                }

                if j.receiver_type == 'employee':
                    e = EmployeeModel.query.get(j.receiver_id)
                    if e:
                        detail.update({
                            "name": e.account_name,
                            "bank_name": e.bank,
                            "bank_account": e.account_number,
                        })

                elif j.receiver_type == 'supplier':
                    s = SupplierModel.query.get(j.receiver_id)
                    if s:
                        detail.update({
                            "name": s.account_name,
                            "bank_name": s.bank,
                            "bank_account": s.account_number,
                        })

                elif j.receiver_type in ('agency', 'university'):
                    a = AgencyModel.query.get(j.receiver_id)
                    if a:
                        detail.update({
                            "name": f"{a.first_name} {a.last_name}",
                            "bank_name": a.bank,
                            "bank_account": a.account_number,
                        })

                elif j.receiver_type == 'organization':
                    o = OrganizationModel.query.get(j.receiver_id)
                    if o:
                        detail.update({
                            "name": o.account_name,
                            "bank_name": o.bank,
                            "bank_account": o.account_number,
                        })

                receiver_detail.append(detail)

        

    children_item = items[0] if items else None

   
    
    return render_template('expense/expense_upgrade_claims.html', segment='expense_claims' ,members=members
                    , users=users, categories=categories, data_supplier=data_supplier, currency=currency , claim=claim,staff_items=items,
                    children_item=children_item,receiver_detail=receiver_detail,children_files=children_files, staff_files=staff_files)

@blueprint.route('/get_user/<int:user_id>')
@login_required
def get_user(user_id):

    result = (
        db.session.query(UserModel, UserProfileModel)
        .outerjoin(UserProfileModel, UserProfileModel.user_id == UserModel.id)
        .filter(UserModel.id == user_id)
        .first()
    )

    if not result:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    user, profile = result   # 👈 สำคัญมาก

    return jsonify({
        'status': 'success',
        'data': {
            'id': user.id,
            'username': user.username,
            'email': profile.email if profile and profile.email else '',
            'phone': profile.phone if profile and profile.phone else '',
            'bank_name': profile.bank_name if profile else '',
            'bank_account': profile.bank_account if profile else '',
            'full_name': (
                f"{profile.first_name} {profile.last_name}"
                if profile and profile.first_name
                else user.username
            )
        }
    })

@blueprint.route('/expense_categories/tree')
@login_required
def expense_category_tree():
    categories = ExpenseCategoryModel.query.filter_by(is_active=True).all()

    data = []
    for cat in categories:
        data.append({
            "id": f"cat-{cat.id}",
            "text": cat.name,
            "type": "category",
            "children": [
                {
                    "id": f"item-{item.id}",
                    "text": item.name,
                    "type": "item",
                    "category_id": cat.id
                }
                for item in cat.subcategories
            ]
        })

    return jsonify(data)

@blueprint.route('/get_member_orders/<int:member_id>')
@login_required
def get_member_orders(member_id):

    orders = (
        OrderModel.query
        .filter(OrderModel.member_id == member_id)
        .all()
    )

    return jsonify({
        'status': 'success',
        'data': [
            {
                'id': o.id,
                'project_id': o.product.id,
                'project_name': o.product.name,
            } for o in orders
        ]
    })


@blueprint.route('/expense/receivers')
@login_required
def get_expense_receivers():
    data = []

    employees = EmployeeModel.query.all()
    # coordinators = CoordinatorModel.query.all()
    organizations = OrganizationModel.query.all()
    agencies = AgencyModel.query.all()
    suppliers = SupplierModel.query.all()

    for e in employees:
        data.append({
            "id": e.id,
            "name": e.name,
            "type": "employee"
        })

    # for c in coordinators:
    #     data.append({
    #         "id": c.id,
    #         "name": c.name,
    #         "type": "coordinator"
    #     })

    for o in organizations:
        data.append({
            "id": o.id,
            "name": o.name,
            "type": "organization"
        })

    for a in agencies:
        data.append({
            "id": a.id,
            "name": a.first_name + " " + a.last_name,   
            "type": "agency"
        })

    for s in suppliers:
        data.append({
            "id": s.id,
            "name": s.name,
            "type": "supplier"
        })
    data = sorted(data, key=lambda x: x["name"].lower())
    return jsonify(data)


def generate_pr_number():
    prefix = 'PR'
    year_month = datetime.now().strftime('%Y%m')  # 202601
    base = f'{prefix}{year_month}-'

    # ดึงเลขล่าสุดของเดือนนี้
    last_number = (
        db.session.query(ExpenseClaim.claim_number)
        .filter(ExpenseClaim.claim_number.like(f'{base}%'))
        .order_by(
            cast(
                func.substring(
                    ExpenseClaim.claim_number,
                    len(base) + 1
                ),
                Integer
            ).desc()
        )
        .first()
    )

    if last_number:
        last_seq = int(last_number[0].split('-')[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    # padding ขั้นต่ำ 5 หลัก (เกินก็ไม่ตัด)
    seq_str = str(next_seq).zfill(5)

    return f'{base}{seq_str}'

def calculate_claim_total(claim: ExpenseClaim):
    total = Decimal('0')

    if claim.claim_type == 'staff':
        items = ExpenseStaffItemModel.query \
            .join(ExpenseClaimStaffModel) \
            .filter(ExpenseClaimStaffModel.claim_id == claim.id) \
            .all()

        for item in items:
            total += Decimal(item.amount or 0)

    elif claim.claim_type == 'children':
        items = ExpenseChildrenItemModel.query \
            .join(ExpenseClaimChildrenModel) \
            .filter(ExpenseClaimChildrenModel.expense_claim_id == claim.id) \
            .all()

        for item in items:
            total += Decimal(item.amount or 0)

    claim.total_amount = total

def parse_date(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%d/%m/%Y")

def to_int(val):
    if val is None:
        return None

    if isinstance(val, str):
        val = val.strip()
        if val.lower() in ("", "none", "null"):
            return None

    try:
        return int(val)
    except (ValueError, TypeError):
        return None




@blueprint.route('/expense/save', methods=['POST'])
@login_required
def save_expense_claim():
    print('Saving expense claim...')
    print(request.form)
    claim_id = request.form.get('claim_id')
    claim_type = request.form.get('claim_type')

    requester_user_id = request.form.get('requester_user_id', type=int)

    if not requester_user_id:
        abort(400, 'Requester is required')

    requester = UserModel.query.get(requester_user_id)
    if not requester:
        return jsonify({
            "status": "error",
            "message": "กรุณาเลือกชื่อ - นามสกุล"
        }), 400
    #     abort(400, 'Invalid requester user')
    # expense_categories = request.form.get('expense_category_id')
    creation_date_str = request.form.get('creation_date')
    creation_date = (datetime.strptime(creation_date_str, '%d/%m/%Y').date() if creation_date_str else None)

    if claim_id:
        # ---- edit existing claim ----
        claim = ExpenseClaim.query.get(claim_id)
        is_update = True
    else:
        claim = ExpenseClaim(
            claim_number=generate_pr_number(),
            claim_type=claim_type,
            requester_user_id=requester_user_id,
            date_created=creation_date,
            # total_amount=staff_total_amount,
        )
        
        db.session.add(claim)
        db.session.flush()
        is_update = False
    
    old_claim_type = claim.claim_type

    claim.claim_type = claim_type
    claim.requester_user_id = requester_user_id
    claim.date_created = creation_date

    if is_update and old_claim_type != claim_type:

        if old_claim_type == 'staff':
            delete_staff_claim(claim.id)

        elif old_claim_type == 'children':
            delete_children_claim(claim.id)


    if claim_type == 'staff':
        save_staff_claim(claim, is_update)

    elif claim_type == 'children':
        save_children_claim(claim, is_update)

    # else:
    #     abort(400, 'Invalid claim type')
    calculate_claim_total(claim)

    db.session.commit()
    return jsonify({'status': 'success'})

def save_staff_claim(claim, is_update=False):

    # ===== header =====
    if is_update and claim.staff_claim:
        staff_claim = claim.staff_claim
    else:
        staff_claim = ExpenseClaimStaffModel(
            claim=claim,
            staff_user_id=to_int(request.form.get('requester_user_id')),
        )
        db.session.add(staff_claim)
        db.session.flush()

    # staff_claim.staff_user_id = to_int(request.form.get('requester_user_id'))
    staff_claim.expense_date = parse_date(request.form.get('expense_date'))
    staff_claim.expense_category_id = to_int(request.form.get('expense_category_id'))
    staff_claim.expense_subcategory_id = to_int(request.form.get('expense_subcategory_id'))
    staff_claim.description = request.form.get('description_staff')

   

    # ===== items =====
    item_ids = request.form.getlist('expense_staff_items_id[]')   # 👈 สำคัญ
    item_names = request.form.getlist('item_name[]')
    amounts = request.form.getlist('staff_amount[]')

    # item เดิมทั้งหมด
    existing_items = {
        item.id: item
        for item in staff_claim.expense_staff_items
    }

    submitted_ids = set()

    for i in range(len(item_names)):
        name = item_names[i]
        amount = amounts[i]
        # item_id = item_ids[i] if i < len(item_ids) else None
        # item_id = to_int(item_ids[i])
        item_id = to_int(item_ids[i]) if i < len(item_ids) else None



        if not name and not amount:
            continue

        if item_id:  # ===== update =====
            item_id = int(item_id)
            submitted_ids.add(item_id)

            item = existing_items.get(item_id)
            if not item:
                continue

            item.item_name = name
            item.amount = amount or 0

        else:  # ===== insert =====
            item = ExpenseStaffItemModel(
                expense_claim_staff_id=staff_claim.id,
                item_name=name,
                amount=amount or 0
            )
            db.session.add(item)

    BASE_UPLOAD_PATH = os.path.join(
        current_app.root_path,
        "static",
        "assets",
        "files",
        "expense"
    )
    # ===== STAFF FILES =====
    staff_files = request.files.getlist('staff_files[]')
    staff_folder = os.path.join(BASE_UPLOAD_PATH, 'staff')
    os.makedirs(staff_folder, exist_ok=True)

    existing_count = ExpenseClaimFileModel.query.filter_by(
        claim_id=claim.id,
        claim_type='staff'
    ).count()

    counter = existing_count + 1

    for f in staff_files:
        if not f or not f.filename:
            continue

        ext = os.path.splitext(f.filename)[1]
        filename = f"{claim.claim_number}_{counter}{ext}"

        filepath = os.path.join(staff_folder, filename)
        f.save(filepath)

        db.session.add(ExpenseClaimFileModel(
            claim_id=claim.id,
            claim_type='staff',
            filename=filename,
            filepath=f"static/assets/files/expense/staff/{filename}"  # 👈 เก็บ path แบบ relative
        ))

        counter += 1
    # ===== delete missing =====
    for item_id, item in existing_items.items():
        if item_id not in submitted_ids:
            db.session.delete(item)


def save_staff_claim2(claim, is_update=False):
    if is_update and claim.staff_claim:
        staff_claim = claim.staff_claim
    else:
        staff_claim = ExpenseClaimStaffModel(claim=claim)
        db.session.add(staff_claim)

    staff_claim.staff_user_id = to_int(request.form.get('requester_user_id'))
    staff_claim.expense_date = parse_date(request.form.get('expense_date'))
    staff_claim.expense_category_id = to_int(request.form.get('expense_category_id'))
    staff_claim.expense_subcategory_id = to_int(request.form.get('expense_subcategory_id'))


    # 🔥 ล้าง items เก่าแล้วใส่ใหม่
    staff_claim.expense_staff_items.clear()

    item_names = request.form.getlist('item_name[]')
    amounts = request.form.getlist('staff_amount[]')

    for name, amount in zip(item_names, amounts):
        if not name:
            continue
        staff_claim.expense_staff_items.append(
            ExpenseStaffItemModel(
                item_name=name,
                amount=amount or 0
            )
        )

def save_staff_claim1(claim: ExpenseClaim):

    staff_user_id = request.form.get('requester_user_id')
    expense_category_id = request.form.get('expense_category_id')
    expense_subcategory_id = request.form.get('expense_subcategory_id')

    expense_date_str = request.form.get('expense_date')
    expense_date = (
        datetime.strptime(expense_date_str, '%d/%m/%Y').date()
        if expense_date_str else None
    )
    descriptions = request.form.get('description')
    staff_total_amount = Decimal(request.form.get('staff_total_amount', '0'))
    
    staff_total_amount = staff_total_amount if staff_total_amount else Decimal('0.00')

    # 1️⃣ สร้าง ExpenseClaimStaff
    staff_claim = ExpenseClaimStaffModel(
        staff_user_id=staff_user_id,
        claim_id=claim.id,
        expense_category_id=expense_category_id,
        expense_subcategory_id=expense_subcategory_id,
        expense_date=expense_date,
        total_amount=staff_total_amount,
        description=descriptions,
    )
    db.session.add(staff_claim)
    db.session.flush()  # เพื่อให้ staff_claim.id ใช้งานได้

    # 2️⃣ รายการย่อย
    item_names = request.form.getlist('item_name[]')
    amounts = request.form.getlist('staff_amount[]')

    total = Decimal('0.00')

    for i in range(len(item_names)):
        amount = Decimal(amounts[i] or '0')

        item = ExpenseStaffItemModel(
            expense_claim_staff_id=staff_claim.id,
            item_name=item_names[i],
            amount=amount,
        )

        # total += amount
        db.session.add(item)

    # 3️⃣ update ยอดรวม (กันซ้ำ)
    # claim.total_amount = total

def save_children_claim(claim, is_update=False):

    # ===== header =====
    member_id = to_int(request.form.get('member_id'))
    project_id = to_int(request.form.get('project_id'))
    description_children = request.form.get('description_children')
    expense_date_str = request.form.get('pay_date')
    expense_date = (
        datetime.strptime(expense_date_str, '%d/%m/%Y').date()
        if expense_date_str else None
    )

    if not member_id or not project_id:
        return jsonify({
            "status": "error",
            "message": "กรุณาเลือกสมาชิกและโครงการให้ครบถ้วน"
        }), 400
    #     return jsonify({"message": "ข้อมูลไม่ครบถ้วน"}), 400
        # return
    # ===== get or create children_claim =====
    if is_update:
        children_claim = ExpenseClaimChildrenModel.query.filter_by(
            expense_claim_id=claim.id
        ).first()
        if not children_claim:
            # create ใหม่เสมอ ถ้าไม่เจอ
            children_claim = ExpenseClaimChildrenModel(
                expense_claim_id=claim.id
            )
            db.session.add(children_claim)
            db.session.flush()

        # if not children_claim:
        #     abort(404, 'Children claim not found')

        children_claim.member_id = member_id
        children_claim.project_id = to_int(project_id)
        children_claim.description = description_children
        children_claim.expense_date = expense_date
    else:
        children_claim = ExpenseClaimChildrenModel(
            expense_claim_id=claim.id,
            member_id=to_int(member_id),
            project_id=to_int(project_id),
            description=description_children,
            expense_date=expense_date,
        )
        db.session.add(children_claim)
        db.session.flush()

    # ===== items =====
    item_ids = request.form.getlist('expense_item_id[]')
    receivers = request.form.getlist('receiver[]')
    currency_ids = request.form.getlist('currency_id[]')
    amounts = request.form.getlist('amount[]')
    ref_amounts = request.form.getlist('ref_amount[]')
    exchange_rates = request.form.getlist('exchange_rate[]')
    remarks = request.form.getlist('remark[]')

    existing_items = {
        item.id: item
        for item in ExpenseChildrenItemModel.query.filter_by(
            expense_claim_children_id=children_claim.id
        ).all()
    }

    submitted_ids = set()

    loop_len = min(
        len(receivers),
        len(item_ids),
        len(currency_ids),
        len(amounts),
    )

    for i in range(loop_len):
        # if not receivers[i]:
        #     continue

        receiver_type, receiver_id = receivers[i].split(':')
        if not receiver_id:
            continue
        item_id = to_int(item_ids[i])
        

        if item_id:  # ===== update =====
            submitted_ids.add(item_id)
            item = existing_items.get(item_id)
            # if not item:
            #     continue

        else:  # ===== insert =====
            item = ExpenseChildrenItemModel(
                expense_claim_children_id=children_claim.id
            )
            db.session.add(item)

        # shared update
        item.receiver_type = receiver_type
        item.receiver_id = to_int(receiver_id)
        item.currency_id = to_int(currency_ids[i])
        item.amount = Decimal(amounts[i] or 0)
        item.ref_amount = Decimal(ref_amounts[i] or 0) if ref_amounts else None
        item.exchange_rate = Decimal(exchange_rates[i] or 1) if exchange_rates else None
        item.remark = remarks[i]

    BASE_UPLOAD_PATH = os.path.join(
        current_app.root_path,
        "static",
        "assets",
        "files",
        "expense"
    )
    # ===== CHILDREN FILES =====
    children_files = request.files.getlist('children_files[]')

    children_folder = os.path.join(BASE_UPLOAD_PATH, 'children')
    os.makedirs(children_folder, exist_ok=True)

    existing_count = ExpenseClaimFileModel.query.filter_by(
        claim_id=claim.id,
        claim_type='children'
    ).count()

    counter = existing_count + 1


    for f in children_files:
        if not f or not f.filename:
            continue

        ext = os.path.splitext(f.filename)[1]
        filename = f"{claim.claim_number}_{counter}{ext}"

        filepath = os.path.join(children_folder, filename)
        f.save(filepath)

        db.session.add(ExpenseClaimFileModel(
            claim_id=claim.id,
            claim_type='children',
            filename=filename,
            filepath=f"static/assets/files/expense/children/{filename}"
        ))

        counter += 1

    # ===== delete missing =====
    for item_id, item in existing_items.items():
        if item_id not in submitted_ids:
            db.session.delete(item)


def save_children_claim2(claim, is_update=False):
    """
    claim = ExpenseClaim ที่ flush แล้ว
    children มีได้คนเดียว
    """

    # ===== header (children) =====
    member_id = request.form.get('member_id')
    project_id = request.form.get('project_id')
    description_children = request.form.get('description_children')
    total_amount = request.form.get('children_total_amount')
    expense_date_str = request.form.get('pay_date')
    expense_date = (
        datetime.strptime(expense_date_str, '%d/%m/%Y').date()
        if expense_date_str else None
    )

    if not member_id or not project_id:
        abort(400, 'member_id and project_id are required')

    # ===== get or create children_claim =====
    if is_update:
        children_claim = ExpenseClaimChildrenModel.query.filter_by(
            expense_claim_id=claim.id
        ).first()

        if not children_claim:
            abort(404, 'Children claim not found')

        # update header
        children_claim.member_id = member_id
        children_claim.project_id = project_id
        children_claim.description = description_children
        children_claim.expense_date = expense_date
        # children_claim.total_amount = Decimal(total_amount or 0)

        # ลบ item เก่าทั้งหมด
        ExpenseChildrenItemModel.query.filter_by(
            expense_claim_children_id=children_claim.id
        ).delete()

    else:
        children_claim = ExpenseClaimChildrenModel(
            expense_claim_id=claim.id,
            member_id=member_id,
            project_id=project_id,
            description=description_children,
            expense_date=expense_date,
            # total_amount=Decimal(total_amount or 0),
        )
        db.session.add(children_claim)
        db.session.flush()  # เอา children_claim.id

    # ===== items =====
    receivers = request.form.getlist('receiver[]')
    currency_ids = request.form.getlist('currency_id[]')
    amounts = request.form.getlist('amount[]')
    ref_amounts = request.form.getlist('ref_amount[]')
    exchange_rates = request.form.getlist('exchange_rate[]')
    remarks = request.form.getlist('remark[]')

    for i in range(len(receivers)):
        if not receivers[i]:
            return jsonify({
                "status": "error",
                "message": "กรุณาเลือก Supplier "
            }), 400
            # continue

        receiver_type, receiver_id = receivers[i].split(':')

        item = ExpenseChildrenItemModel(
            expense_claim_children_id=children_claim.id,
            receiver_type=receiver_type,
            receiver_id=int(receiver_id),
            currency_id=currency_ids[i],
            amount=Decimal(amounts[i] or 0),
            ref_amount=Decimal(ref_amounts[i] or 0) if ref_amounts else None,
            exchange_rate=Decimal(exchange_rates[i] or 1) if exchange_rates else None,
            remark=remarks[i],
        )

        db.session.add(item)

def save_children_claim1(claim):
    """
    claim = ExpenseClaim ที่ flush แล้ว
    children มีได้คนเดียว
    """

    # ===== header (children) =====
    member_id = request.form.get('member_id')
    project_id = request.form.get('project_id')
    description_children = request.form.get('description_children')
    total_amount = request.form.get('children_total_amount')
    expense_date_str = request.form.get('pay_date')
    expense_date = (
        datetime.strptime(expense_date_str, '%d/%m/%Y').date()
        if expense_date_str else None
    )

    if not member_id or not project_id:
        abort(400, 'member_id and project_id are required')

    children_claim = ExpenseClaimChildrenModel(
        expense_claim_id=claim.id,
        member_id=member_id,
        project_id=project_id,
        description=description_children,
        expense_date=expense_date,
        # total_amount=Decimal(total_amount or 0),

    )
    db.session.add(children_claim)
    db.session.flush()  # เอา children_claim.id

    # ===== items =====
    receivers = request.form.getlist('receiver[]')
    currency_ids = request.form.getlist('currency_id[]')
    # pay_dates = request.form.getlist('pay_date[]')
    amounts = request.form.getlist('amount[]')
    ref_amounts = request.form.getlist('ref_amount[]')
    exchange_rates = request.form.getlist('exchange_rate[]')
    remarks = request.form.getlist('remark[]')

    for i in range(len(receivers)):
        if not receivers[i]:
            continue

        # receiver format: "supplier:3"
        receiver_type, receiver_id = receivers[i].split(':')

        item = ExpenseChildrenItemModel(
            expense_claim_children_id=children_claim.id,
            receiver_type=receiver_type,
            receiver_id=int(receiver_id),
            currency_id=currency_ids[i],
            # pay_date=datetime.strptime(pay_dates[i], '%d/%m/%Y').date()
            #          if pay_dates[i] else None,
            amount=Decimal(amounts[i] or 0),
            ref_amount=Decimal(ref_amounts[i] or 0) if ref_amounts else None,
            exchange_rate=Decimal(exchange_rates[i] or 1) if exchange_rates else None,
            remark=remarks[i],
        )

        db.session.add(item)

def delete_staff_claim(claim_id):

    staff_claim = ExpenseClaimStaffModel.query.filter_by(
        claim_id=claim_id
    ).first()

    if not staff_claim:
        return

    # 1️⃣ ลบ items ก่อน
    ExpenseStaffItemModel.query.filter_by(
        expense_claim_staff_id=staff_claim.id
    ).delete(synchronize_session=False)

    # 2️⃣ ลบ staff claim
    db.session.delete(staff_claim)

    db.session.flush()


def delete_children_claim(claim_id):

    children_claim = ExpenseClaimChildrenModel.query.filter_by(expense_claim_id=claim_id).first()
    if not children_claim:
        return
    
    ExpenseChildrenItemModel.query.filter_by(
        expense_claim_children_id=children_claim.id
    ).delete(synchronize_session=False)
    db.session.flush()


@blueprint.route('/delete_claim/<int:claim_id>', methods=['DELETE'])
@login_required
@delete_permission.require(http_exception=403)
def delete_claim(claim_id):
    print(claim_id)
    try:
        claim = ExpenseClaim.query.get(claim_id)
        if not claim:
            return jsonify({
                'status': 'error',
                'message': 'Currency not found.'
            }), 404


        db.session.delete(claim)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Deleted successfully.'
        })

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    

@blueprint.route('/downloadFileStaff/<filename>')
def downloadFileStaff(filename):

    file = ExpenseClaimFileModel.query.filter_by(filename=filename).first()
    if not file:
        abort(404, description="File record not found in database")

    # ใช้ filepath จาก DB โดยตรง
    file_path = os.path.join(current_app.root_path, file.filepath)

    # file_path = file.filepath

    if not os.path.exists(file_path):
        abort(404, description="File not found on server")

    # return send_file(file_path, as_attachment=True)
    return send_file(file_path)

@blueprint.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    id_file = request.form["id_file"]
    type_staff = request.form["type_staff"]
    claim_id = request.form["claim_id"]


    thisFile = ExpenseClaimFileModel.query.filter_by(id=id_file).first()

    print("CWD:", os.getcwd())
    print("FILEPATH:", thisFile.filepath)

    file_path = thisFile.filepath

    try:
        if not os.path.isabs(file_path):
            file_path = os.path.join(current_app.root_path, file_path)

        print("REAL PATH:", file_path)

        if os.path.exists(file_path):
            os.remove(file_path)
        
        else:
            print(f"ไม่พบไฟล์ในระบบไฟล์: {file_path}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")

    db.session.delete(thisFile)
    db.session.commit()

    return redirect(url_for('account_blueprint.expense_upgrade_claims', claim_id=claim_id))
