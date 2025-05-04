from flask import Blueprint

blueprint = Blueprint(
    'coordinator_blueprint',
    __name__,
    url_prefix='/coordinator'
)
