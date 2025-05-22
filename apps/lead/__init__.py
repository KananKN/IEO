from flask import Blueprint

blueprint = Blueprint(
    'lead_blueprint',
    __name__,
    url_prefix='/lead'
)
