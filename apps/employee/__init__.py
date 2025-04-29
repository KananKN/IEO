from flask import Blueprint

blueprint = Blueprint(
    'sponsor_blueprint',
    __name__,
    url_prefix='/sponsor'
)
