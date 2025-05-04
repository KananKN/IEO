
import time
import re
from apps.coordinator import blueprint
from apps.authentication.models import *
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

read_permission = Permission(RoleNeed("read_coordinator"))
write_permission = Permission(RoleNeed("write_coordinator"))
delete_permission = Permission(RoleNeed("delete_coordinator"))


# ---------- Fees ------------------------s
@blueprint.route('/')
@login_required
@read_permission.require(http_exception=403)
def coordinator():
    datas = EmployeeModel.query.all()
    # print(datas)
    return render_template('employee/employee.html', segment='coordinator' ,datas=datas, )
