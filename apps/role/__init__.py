from flask import Blueprint

blueprint = Blueprint(
    'role_blueprint',
    __name__,
    url_prefix='/setting/role'
)
