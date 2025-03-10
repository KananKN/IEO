from flask import Blueprint

blueprint = Blueprint(
    'product_blueprint',
    __name__,
    url_prefix='/product'
)
