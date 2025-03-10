
from apps.home import blueprint
from flask import render_template, request, jsonify, redirect
from flask_login import login_required
from jinja2 import TemplateNotFound
import requests
from datetime import datetime
from sqlalchemy import text
from apps import db, login_manager


@blueprint.route('/home')
@login_required
def index():
    return render_template('home/index.html', segment='index')


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
