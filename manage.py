from flask.cli import FlaskGroup

# from apps import app, db
from apps.authentication.models import *
from run import app, db
from sqlalchemy import text

import psycopg2

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    resources = ["user", "role", "permission", "resource", "clinical dashboard"]
    permissions = ["read", "write", "delete"]
    roles = ["Admin", "User", "Guest"]
    users = ["admin", "user", "guest"]
    
    # Admin role can do anything on any resource
    admin_role_permission = [
        {"role": "Admin", "permission": "read", "resource": "user"},
        {"role": "Admin", "permission": "write", "resource": "user"},
        {"role": "Admin", "permission": "delete", "resource": "user"},
        {"role": "Admin", "permission": "read", "resource": "role"},
        {"role": "Admin", "permission": "write", "resource": "role"},
        {"role": "Admin", "permission": "delete", "resource": "role"},
        {"role": "Admin", "permission": "read", "resource": "permission"},
        {"role": "Admin", "permission": "write", "resource": "permission"},
        {"role": "Admin", "permission": "delete", "resource": "permission"},
        {"role": "Admin", "permission": "read", "resource": "resource"},
        {"role": "Admin", "permission": "write", "resource": "resource"},
        {"role": "Admin", "permission": "delete", "resource": "resource"},
        {"role": "Admin", "permission": "read", "resource": "clinical dashboard"},
        {"role": "Admin", "permission": "write", "resource": "clinical dashboard"},
        {"role": "Admin", "permission": "delete", "resource": "clinical dashboard"},
    ]
    
    # User role can read and write on all resource
    user_role_permission = [
        {"role": "User", "permission": "read", "resource": "user"},
        {"role": "User", "permission": "write", "resource": "user"},
        {"role": "User", "permission": "read", "resource": "role"},
        {"role": "User", "permission": "write", "resource": "role"},
        {"role": "User", "permission": "read", "resource": "permission"},
        {"role": "User", "permission": "write", "resource": "permission"},
        {"role": "User", "permission": "read", "resource": "resource"},
        {"role": "User", "permission": "write", "resource": "resource"},
    ]
    
    # Guest role can only read on all resource
    guest_role_permission = [
        {"role": "Guest", "permission": "read", "resource": "user"},
        {"role": "Guest", "permission": "read", "resource": "role"},
        {"role": "Guest", "permission": "read", "resource": "permission"},
        {"role": "Guest", "permission": "read", "resource": "resource"},
    ]
    
    # Insert Resource
    resource1 = ResourceModel(name="user", description="User Resource")
    resource2 = ResourceModel(name="role", description="Role Resource")
    resource3 = ResourceModel(name="permission", description="Permission Resource")
    resource4 = ResourceModel(name="resource", description="Resource Resource")
    resource5 = ResourceModel(name="clinical dashboard", description="Clinical Dashboard Resource")
    db.session.add_all([resource1, resource2, resource3, resource4, resource5])
    db.session.commit()
    
    # Insert Role
    for role in roles:
        role = RoleModel(name=role, description=f"{role} Role")
        db.session.add(role)
        db.session.commit()
    
    # Insert Permissions
    for resource in resources:
        for per in permissions:
            permission = PermissionModel(name=per, resource_id=ResourceModel.query.filter_by(name=resource).first().id, description=f"{per} {resource}")
            db.session.add(permission)
            db.session.commit()
            
    # Insert admin permission
    for role_permission in admin_role_permission:
        resource_id = ResourceModel.query.filter_by(name=role_permission["resource"]).first().id
        permission_id = PermissionModel.query.filter_by(name=role_permission["permission"]).filter_by(resource_id=resource_id).first().id
        role_id = RoleModel.query.filter_by(name=role_permission["role"]).first().id
        role_permission = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id)
        db.session.add(role_permission)
        db.session.commit()
    
    # Insert user permission
    for role_permission in user_role_permission:
        resource_id = ResourceModel.query.filter_by(name=role_permission["resource"]).first().id
        permission_id = PermissionModel.query.filter_by(name=role_permission["permission"]).filter_by(resource_id=resource_id).first().id
        role_id = RoleModel.query.filter_by(name=role_permission["role"]).first().id
        role_permission = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id)
        db.session.add(role_permission)
        db.session.commit()
    
    # Insert guest permission
    for role_permission in guest_role_permission:
        resource_id = ResourceModel.query.filter_by(name=role_permission["resource"]).first().id
        permission_id = PermissionModel.query.filter_by(name=role_permission["permission"]).filter_by(resource_id=resource_id).first().id
        role_id = RoleModel.query.filter_by(name=role_permission["role"]).first().id
        role_permission = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id)
        db.session.add(role_permission)
        db.session.commit()

    # Insert User
    for user in users:
        user = UserModel(username=user, password="123456", role_id=RoleModel.query.filter(RoleModel.name.ilike(user)).first().id)    
        db.session.add(user)
        db.session.commit()
    

if __name__ == "__main__":
    cli()
