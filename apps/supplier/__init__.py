from flask import Blueprint

blueprint = Blueprint(
    'supplier_blueprint',
    __name__,
    url_prefix='/supplier'
)
