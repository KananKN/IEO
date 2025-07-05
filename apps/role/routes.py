
import time
import re
from apps.role import blueprint
from apps.authentication.models import *
from apps import db
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
from sqlalchemy import not_

read_permission = Permission(RoleNeed("read_role"))
write_permission = Permission(RoleNeed("write_role"))
delete_permission = Permission(RoleNeed("delete_role"))

@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = RoleModel.query.all()
    resources = ResourceModel.query.all()
    permissions = PermissionModel.query.all()
    # print(datas)
    return render_template('usermanage/role.html', segment='role' ,datas=datas, resources=resources, permissions=permissions)

@blueprint.route('/add', methods=['POST'])
@login_required
def add():
    print(request.form)
    name = request.form.get("name")
    description = request.form.get("description")
    # resource_id = request.form.get("resource_id")
    name_check = RoleModel.query.filter_by(name=name).first()
    if not name_check :
        newItem = RoleModel(name=name, description=description)
        db.session.add(newItem)
        db.session.commit()
        permissions = PermissionModel.query.all()
        for permission in permissions:
            if request.form.get(str(permission.id)):
                newItem.permissions.append(permission)
        db.session.commit()
        flash("Add success!", "success")
    else:
        flash("Already registered!", "danger")
    return redirect(url_for('role_blueprint.index'))

@blueprint.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    thisItem = RoleModel.query.filter_by(id=id).first()
    name = thisItem.name
    db.session.query(RolePermissionModel).filter(
        RolePermissionModel.role_id == id).delete()
    db.session.commit()
    db.session.query(RoleModel).filter(
        RoleModel.id == id).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('role_blueprint.index'))

@blueprint.route('/update', methods=['POST'])
@login_required
def update():
    # print(request.form)
    id = request.form["id"]
    name = request.form["name"]
    description = request.form["description"]
    name_check = RoleModel.query.filter_by(name=name).first()
    if name_check:
        if name_check.id != int(id):
            flash("Already registered!", "danger")
            return redirect(url_for('role_blueprint.index'))
    thisItem = RoleModel.query.filter_by(id=id).first()
    thisItem.name = name
    thisItem.description = description
    db.session.commit()
    # delete all permissions
    thisItem.permissions = []
    permissions = PermissionModel.query.all()
    for permission in permissions:
        if request.form.get(str(permission.id)):
            thisItem.permissions.append(permission)
    db.session.commit()
    flash("Update success!", "success")
    return redirect(url_for('role_blueprint.index'))
