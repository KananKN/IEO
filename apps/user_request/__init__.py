from flask import Blueprint

blueprint = Blueprint(
    'userRequest_blueprint',
    __name__,
    url_prefix='/user_request'
)
