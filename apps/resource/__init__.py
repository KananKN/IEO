from flask import Blueprint

blueprint = Blueprint(
    'resource_blueprint',
    __name__,
    url_prefix='/setting/resource'
)
