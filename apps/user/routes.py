
import time
import re
from apps.user import blueprint
from apps.authentication.models import *
from apps import db
from apps.authentication.util import hash_pass

from flask import render_template, request, redirect, url_for, flash, Markup, jsonify, abort
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

read_permission = Permission(RoleNeed("read_user"))
write_permission = Permission(RoleNeed("write_user"))
delete_permission = Permission(RoleNeed("delete_user"))

@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = UserModel.query.all()
    print(datas)
    roles = RoleModel.query.all()
    # print(datas)
    return render_template('usermanage/user.html', segment='user' ,datas=datas, roles=roles)

@blueprint.route('/add', methods=['POST'])
@login_required
def add():
    print(request.form)
    username = request.form.get("username")
    password = request.form.get("password")
    role_id = request.form.get("role_id")
    name_check = UserModel.query.filter_by(username=username).first()
    if not name_check :
        newItem = UserModel(username=username, password=password, role_id=role_id)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    else:
        flash("Already registered!", "danger")
    return redirect(url_for('user_blueprint.index'))

@blueprint.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    thisItem = UserModel.query.filter_by(id=id).first()
    name = thisItem.username
    db.session.query(UserModel).filter(
        UserModel.id == id).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('user_blueprint.index'))

@blueprint.route('/update', methods=['POST'])
@login_required
def update():
    # print(request.form)
    id = request.form["id"]
    username = request.form["username"]
    password = request.form["password"]
    role_id = request.form["role_id"]
    username_check = UserModel.query.filter_by(username=username).first()
    if username_check:
        if username_check.id != int(id):
            flash("Already registered!", "danger")
            return redirect(url_for('user_blueprint.index'))
    thisItem = UserModel.query.filter_by(id=id).first()
    thisItem.username = username
    if password:
         thisItem.password = hash_pass(password)
    thisItem.role_id = role_id
    db.session.commit()
    flash("Update success!", "success")
    return redirect(url_for('user_blueprint.index'))
