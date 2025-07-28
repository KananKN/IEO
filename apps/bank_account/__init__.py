from flask import Blueprint

blueprint = Blueprint(
    'bank_account_blueprint',
    __name__,
    url_prefix='/bank_account'
)
