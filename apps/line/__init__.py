from flask import Blueprint

blueprint = Blueprint(
    'line_blueprint',
    __name__,
    url_prefix='/line'
)
