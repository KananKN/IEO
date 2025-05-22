

import time
import re
from apps.agency import blueprint
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


@blueprint.route('/create_agency')
@login_required
def create_agency():
    return render_template('agency/agency_create.html', segment='create_agency')


@blueprint.route('/dashboard')
@login_required
def dashboard():
    return render_template('home/dashboard.html', segment='dashboard')


def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
