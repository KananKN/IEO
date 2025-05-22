from flask import Blueprint

blueprint = Blueprint(
    'order_blueprint',
    __name__,
    url_prefix='/order'
)
