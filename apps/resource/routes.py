
import time
import re
from apps.resource import blueprint
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

read_permission = Permission(RoleNeed("read_resource"))
write_permission = Permission(RoleNeed("write_resource"))
delete_permission = Permission(RoleNeed("delete_resource"))

@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def index():
    datas = ResourceModel.query.all()
    # print(datas)
    return render_template('usermanage/resource.html', segment='resource' ,datas=datas)

@blueprint.route('/add', methods=['POST'])
@login_required
def add():
    print(request.form)
    name = request.form.get("name")
    description = request.form.get("description")
    name_check = ResourceModel.query.filter_by(name=name).first()
    if not name_check:
        newItem = ResourceModel(name=name, description=description)
        db.session.add(newItem)
        db.session.commit()
        flash("Add success!", "success")
    else:
        flash("Already registered!", "danger")
    return redirect(url_for('resource_blueprint.index'))

@blueprint.route('/delete', methods=['POST'])
@login_required
def delete():
    id = request.form["id"]
    thisItem = ResourceModel.query.filter_by(id=id).first()
    name = thisItem.name
    db.session.query(ResourceModel).filter(
        ResourceModel.id == id).delete()
    db.session.commit()
    flash(name+' Deleted!', 'success')
    return redirect(url_for('resource_blueprint.index'))

@blueprint.route('/update', methods=['POST'])
@login_required
def update():
    # print(request.form)
    id = request.form["id"]
    name = request.form["name"]
    description = request.form["description"]
    name_check = ResourceModel.query.filter_by(name=name).first()
    if name_check:
        if name_check.id != int(id):
            flash("Already registered!", "danger")
            return redirect(url_for('resource_blueprint.index'))
    thisItem = ResourceModel.query.filter_by(id=id).first()
    thisItem.name = name
    thisItem.description = description
    db.session.commit()
    flash("Update success!", "success")
    return redirect(url_for('resource_blueprint.index'))

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
