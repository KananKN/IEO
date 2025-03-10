
from flask_principal import RoleNeed, identity_loaded, Principal
from flask_login import login_required, current_user

# from apps.authentication.models import *

principal = Principal()

# Define a function to load the user's identity
@identity_loaded.connect
def on_identity_loaded(sender, identity):
    # Get User
    # user = UserModel.query.filter_by(id=identity.id).first()
    user = current_user if current_user.is_authenticated else None
    
    # Get all unique permissions
    # for role in user.roles:
        # get permission
    if user is None:
        return
    for permission in user.role.permissions:
        # Add the user's roles to the identity object
        identity.provides.add(RoleNeed(f"{permission.name}_{permission.resource.name}"))

