from flask import Blueprint

blueprint = Blueprint(
    'employee_blueprint',
    __name__,
    url_prefix='/employee'
)
