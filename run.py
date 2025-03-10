# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_cors import CORS

import os
from flask_migrate import Migrate
from flask_minify import Minify
from sys import exit

from apps.config import config_dict
from apps import create_app, db
from flask_login import login_required, current_user
from flask import request, redirect, url_for
from datetime import datetime

from flask import render_template

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')
DEBUG = 'True'
# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:

    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)
CORS(app, origins=['*'])
Migrate(app, db)

@app.errorhandler(401)
def access_forbidden(error):
    return redirect(url_for('authentication_blueprint.login'))

@app.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500

# @app.before_request
# def log_request_info():
#     # print('Body: %s', request.get_data())
#     if current_user.is_authenticated:
#         if 'static' not in request.path:
#             # print('Headers: %s', request.path)
#             dt = datetime.now()
#             eventName = ""
#             if request.path == "/online_data":
#                 eventName = "Online data"
#             if request.path == "/historical_data":
#                 eventName = "Historical data"
#             if request.path == "/setting/datalogger/dataloggermanage":
#                 eventName = "Datalogger management"
#             if request.path == "/setting/meter/metermanage":
#                 eventName = "Meter management"
#             if request.path == "/setting/location/excelimport":
#                 eventName = "Excel import"
#             if request.path == "/setting/location/locationmanage":
#                 eventName = "Tree view"
#             if request.path == "/setting/usermanage":
#                 eventName = "User management"
#             if request.path == "/setting/permission/":
#                 eventName = "Permission management"
#             check = Users_Log.query.filter_by(created_at=dt).filter_by(
#                 user_id=current_user.id).first()
#             if not check and eventName != "":
#                 print('Headers: %s', request.path)
#                 newlog = Users_Log(eventName, current_user.id, dt)
#                 db.session.add(newlog)
#                 db.session.commit()


if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info('ASSETS_ROOT = ' + app_config.ASSETS_ROOT)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5003)