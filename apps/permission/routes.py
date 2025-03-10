
import time
import re
from apps.permission import blueprint
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

# @blueprint.route('/update', methods=['POST'])
# @login_required
# def update():
#     jsonData = request.get_json()
#     print(jsonData)
#     checkLine = Line.query.first()
#     if checkLine:
#         checkLine.token = jsonData["token"]
#         db.session.commit()
#         return jsonify({"data": "success"})
#     else:
#         new = Line(jsonData["token"])
#         db.session.add(new)
#         db.session.commit()
#         return jsonify({"data": "success"})


# @blueprint.route('/send_message', methods=['POST'])
# @login_required
# def send_message():
#     jsonData = request.get_json()
#     # print(jsonData)
#     base64_data = re.sub('^data:image/.+;base64,', '', jsonData["img"])
#     byte_data = base64.b64decode(base64_data)
#     image_data = BytesIO(byte_data)
#     img = Image.open(image_data)
#     t = time.time()
#     image_path = "image" + str(t) + '.png'
#     img.save(image_path, "PNG")
#     checkLine = Line.query.first()
#     if not checkLine:
#         return jsonify({"data": "Token is not registered!"}), 400
#     """Send a LINE Notify message (with or without an image)."""
#     URL = 'https://notify-api.line.me/api/notify'
#     headers = {'Authorization': 'Bearer ' + checkLine.token}
#     payload = {'message': jsonData["msg"]}
#     files = {'imageFile': open(image_path, 'rb')}
#     r = requests.post(URL, headers=headers, params=payload, files=files)
#     print(r.content)
#     return jsonify({"data": "success", "status": r.status_code})
