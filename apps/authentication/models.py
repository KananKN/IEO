from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass
from flask import jsonify

from dataclasses import dataclass

@dataclass
class UserModel(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id: int
    username: str
    password: str
    role_id: int

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    # email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete='SET NULL'))
    
    # oauth_github  = db.Column(db.String(100), nullable=True)
    # user_manage_permission = db.Column(db.Boolean, default=False)
    # meter_manage_permission = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)
    
    # def get_role_permission_to_str(self):
    #     role = RoleModel.query.filter_by(id=self.role_id).first()
    #     permissions = role.permissions
    #     return [permission.name+"_"+permission.resource.name for permission in permissions]

    def has_permission(self, permission):
        role = RoleModel.query.filter_by(id=self.role_id).first()
        permissions = role.permissions
        return permission in [permission.name+"_"+permission.resource.name for permission in permissions]
    
@login_manager.user_loader
def user_loader(id):
    return UserModel.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = UserModel.query.filter_by(username=username).first()
    return user if user else None


# class OAuth(OAuthConsumerMixin, db.Model):
#     user_id = db.Column(db.Integer, db.ForeignKey(
#         "Users.id", ondelete="cascade"), nullable=False)
#     user = db.relationship(Users)

@dataclass
class RoleModel(db.Model):
    __tablename__ = "role"
    
    id: int
    name: str
    description: str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String(), nullable=False)
    permissions = db.relationship(
        "PermissionModel", back_populates="roles", secondary="role_permission", cascade="all, delete"
    )
    users = db.relationship(
        "UserModel", backref="role", cascade="all, delete", lazy=True
    )

@dataclass
class PermissionModel(db.Model):
    __tablename__ = "permission"
    id: int
    name: str
    description: str
    resource_id: int
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    roles = db.relationship(
        "RoleModel", back_populates="permissions", secondary="role_permission", cascade="all, delete"
    )
    
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id", ondelete='CASCADE'))
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

@dataclass
class RolePermissionModel(db.Model):
    __tablename__ = "role_permission"
    id: int
    role_id: int
    permission_id: int
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete='CASCADE'))
    permission_id = db.Column(db.Integer, db.ForeignKey("permission.id", ondelete='CASCADE'))
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

@dataclass
class ResourceModel(db.Model):
    __tablename__ = "resource"
    id: int
    name: str
    description: str
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String())
    permissions = db.relationship(
        "PermissionModel", backref="resource", cascade="all, delete", lazy=True
    )
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

