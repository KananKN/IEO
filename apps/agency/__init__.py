from flask import Blueprint

blueprint = Blueprint(
    'agency_blueprint',
    __name__,
    url_prefix='/agency'
)
