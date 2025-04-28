from flask import Blueprint

blueprint = Blueprint(
    'organization_blueprint',
    __name__,
    url_prefix='/organization'
)
