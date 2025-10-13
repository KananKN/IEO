from flask import Blueprint

blueprint = Blueprint(
    'notification_blueprint',
    __name__,
    url_prefix='/notification'
)
