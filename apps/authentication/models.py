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
    status = db.Column(db.String(20), default='pending') 
    
    agency = db.relationship(
    'AgencyModel',
    back_populates='user',
    foreign_keys='AgencyModel.user_id',
    uselist=False)
    
    
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'status': self.status,
            # เพิ่มเฉพาะ field ที่ต้องการส่งกลับ
        }
    
   
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


@dataclass
class AgencyModel(db.Model):
    __tablename__ = 'agency'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True)

    company_name_en = db.Column(db.String(100))
    company_name_th = db.Column(db.String(100))
    address = db.Column(db.Text)
    currency = db.Column(db.String(10))
    file_id = db.Column(db.String(100))
    country_id = db.Column(db.Integer)
    tel = db.Column(db.String(30))
    email = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    status = db.Column(db.String(20))  # pending / approved / rejected
    web = db.Column(db.String(100))
    
    is_agency = db.Column(db.Boolean, default=False)
    agency_code = db.Column(db.String(20), unique=True, nullable=True)

    # ใครแนะนำมา
    # referred_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    org_type = db.Column(db.String(100))
    tax_id = db.Column(db.String(50))
    country = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    referred_by_id = db.Column(db.Integer, db.ForeignKey('agency.id'), nullable=True)


    # user = db.relationship('UserModel',back_populates='agency',foreign_keys=[user_id],uselist=False)
    user = db.relationship('UserModel',back_populates='agency',foreign_keys=[user_id], uselist=False,cascade="all, delete"
)
    referred_by = db.relationship('AgencyModel', foreign_keys=[referred_by_id], remote_side=[id], backref='referrals', uselist=False)

    
    status_company = db.Column(db.Integer, comment='1:headquarters,2:branch')
    zip_code = db.Column(db.String(), nullable=False,server_default='00000')
    shipping_address = db.Column(db.String(), nullable=True)
    office_number = db.Column(db.String(), nullable=True)
    fax_number = db.Column(db.String(), nullable=True)
    bank = db.Column(db.String(), nullable=True)
    account_number = db.Column(db.String(), nullable=True)
    bank_branch = db.Column(db.String(), nullable=True)
    type_bank = db.Column(db.Integer, nullable=True, comment='1:savings,2:daily_current')
    foreign_banks = db.Column(db.String(), nullable=True)
    swiftCode = db.Column(db.String(), nullable=True)
    bank_address = db.Column(db.String(), nullable=True)
    note = db.Column(db.String(), nullable=True)
    account_name = db.Column(db.String(), nullable=True)
    foreign_banks_name = db.Column(db.String(), nullable=True)
    # interested_users = db.relationship("interestedUsersModel", back_populates="agency", lazy=True)
    lead = db.relationship("leadModel", back_populates="agency", lazy=True)
    lead_programs = db.relationship("LeadProgram", back_populates="agency", overlaps="products,agency")
    orders = db.relationship("OrderModel", back_populates="agency", lazy=True, passive_deletes=True)



    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
@dataclass        
class ProductAgencyAssociation(db.Model):
    __tablename__ = 'product_agency_association'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product_for_sales.id', ondelete='CASCADE'))
    agency_id = db.Column(db.Integer, db.ForeignKey('agency.id' , ondelete='CASCADE'))

    # ข้อมูลเพิ่มเติมที่อยากเก็บ (optional)
    status = db.Column(db.String(20), default='active')  # active, pending
    assigned_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.Text)

    product = db.relationship('ProductForSalesModel', backref='agency_links')
    employee = db.relationship('AgencyModel', backref='product_links')    
    
    
   




