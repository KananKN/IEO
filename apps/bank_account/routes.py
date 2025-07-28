
import time
import re
from apps.bank_account import blueprint
from apps.authentication.models import *
from apps.bank_account.models import *
from apps.order.models import *
from apps.supplier.models import *
from apps.employee.models import *
from apps.lead.models import *
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




read_permission = Permission(RoleNeed("read_bank account"))
write_permission = Permission(RoleNeed("write_bank account"))
delete_permission = Permission(RoleNeed("delete_bank account"))


@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = BankAccountModel.query.all()
    # print(datas)
    return render_template('bank_account/bank_account.html', segment='bank_account' ,datas=datas)



@blueprint.route('/addBank', methods=['POST'])
@login_required
def addBank():
    data = request.get_json()
    print(data)
    name = data.get("name", "").strip()
    account_no = data.get("account_no", "").strip()

    if not account_no:
        return jsonify({"success": False, "message": "กรุณากรอกหมายเลขบัญชี"}), 400

    existing = BankAccountModel.query.filter_by(account_number=account_no).first()
    if existing:
        return jsonify({"success": False, "message": "หมายเลขบัญชีนี้ถูกใช้แล้ว"}), 409

    newItem = BankAccountModel(name=name, account_number=account_no)
    db.session.add(newItem)
    db.session.commit()

    return jsonify({"success": True, "message": "เพิ่มบัญชีสำเร็จ"}), 201



@blueprint.route('/deleteBank', methods=['POST'])
@login_required
def deleteBank():
    id = request.form["id"]
    thisItem = BankAccountModel.query.filter_by(id=id).first()
    db.session.query(BankAccountModel).filter(
        BankAccountModel.id == id).delete()
    db.session.commit()
    flash(' Deleted!', 'success')
    return redirect(url_for('bank_account_blueprint.index'))

@blueprint.route('/updateBank', methods=['POST'])
@login_required
def updateBank():
    # print(request.form)
    data = request.get_json()

    id = data.get("id")
    name = data.get("name")
    account_no = data.get("account_no")

    # ตรวจสอบว่ามี Bank ที่ต้องการอัปเดตอยู่จริง
    thisItem = BankAccountModel.query.filter_by(id=id).first()
    if thisItem:
        # 🔍 ตรวจสอบว่ามี account_number ซ้ำกับ id อื่นหรือไม่
        duplicate = BankAccountModel.query.filter(
            BankAccountModel.account_number == account_no,
            BankAccountModel.id != id
        ).first()

        if duplicate:
            return jsonify({"success": False, "message": "หมายเลขบัญชีนี้ถูกใช้แล้ว."}), 409

        thisItem.name = name
        thisItem.account_number = account_no
        db.session.commit()
        return jsonify({"success": True, "message": "Update success!"}), 200
    else:
        return jsonify({"success": False, "message": "Bank account not found."}), 404



   
   




