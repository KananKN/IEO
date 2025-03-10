from flask import Blueprint

blueprint = Blueprint(
    'permission_blueprint',
    __name__,
    url_prefix='/setting/permission'
)
