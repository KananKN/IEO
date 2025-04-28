from flask import Blueprint

blueprint = Blueprint(
    'univercity_blueprint',
    __name__,
    url_prefix='/univercity'
)
