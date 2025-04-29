from flask import Blueprint

blueprint = Blueprint(
    'university_blueprint',
    __name__,
    url_prefix='/university'
)
