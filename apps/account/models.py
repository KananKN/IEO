from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey

class ExpenseCategoryModel(db.Model):
    __tablename__ = "expense_categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    

    is_active = db.Column(db.Boolean, default=True)
    admin_only = db.Column(db.Boolean,default=False)
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # ✅ เพิ่ม relationship + cascade
    subcategories = db.relationship(
        "ExpenseSubCategoryModel",
        back_populates="category",
        cascade="all, delete-orphan"
    )
   

    def __repr__(self):
        return f"<ExpenseCategory id={self.id}  name={self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "admin_only": self.admin_only,
            
        }

class ExpenseSubCategoryModel(db.Model):
    __tablename__ = "expense_subcategories"

    id = db.Column(db.Integer, primary_key=True)

    expense_category_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_categories.id"),
        nullable=False
    )

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # amount = db.Column(db.Numeric(12, 2), nullable=False)

    # currency = db.Column(db.String(10), default="THB")
    # exchange_rate = db.Column(db.Numeric(10, 4))
    # amount_thb = db.Column(db.Numeric(12, 2))

    paid_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # 🔗 relationship
    category = db.relationship(
        "ExpenseCategoryModel",
        back_populates="subcategories"
    )

    def __repr__(self):
        # return f"<ExpenseItem {self.name} {self.amount}>"
        return f"<ExpenseItem {self.name} id_sub={self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.expense_category_id,
            # "amount": float(self.amount),
            # "currency": self.currency,
            # "amount_thb": float(self.amount_thb) if self.amount_thb else None
        }

class CurrencyModel(db.Model):
    __tablename__ = "currencies"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(10), nullable=False)   # THB, USD
    name = db.Column(db.String(50), nullable=False)               # Thai Baht
    # symbol = db.Column(db.String(10))                             # ฿, $
    
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
           
        }
    
class ExpenseClaim(db.Model):
    __tablename__ = 'expense_claims'

    id = db.Column(db.Integer, primary_key=True)
    claim_number = db.Column(db.String(50), unique=True, nullable=False)
    claim_type = db.Column(db.String(20), nullable=True)  # staff | children

    requester_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    requester = db.relationship('UserModel', backref='expense_claims')

    total_amount = db.Column(db.Numeric(12,2))
    status = db.Column(db.String(20), default='draft')
    description = db.Column(db.Text)
    date_created = db.Column(db.Date, default=db.func.current_date())

    # admin_only = db.Column(db.Boolean,default=False)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    staff_claim = db.relationship(
        'ExpenseClaimStaffModel',
        back_populates='claim',
        uselist=False,
        cascade='all, delete-orphan'
    )

    children_claim = db.relationship(
        'ExpenseClaimChildrenModel',
        back_populates='expense_claims',
        uselist=True,
        cascade='all, delete-orphan'
    )
    files = db.relationship(
        'ExpenseClaimFileModel',
        cascade='all, delete-orphan'
    )
    @property
    def paid_date(self):
        if self.claim_type == 'staff' and self.staff_claim:
            return self.staff_claim.expense_date

        if self.claim_type == 'children' and self.children_claim:
            # children อาจมีหลายรายการ → เลือกตาม business logic
            return self.children_claim[0].expense_date if self.children_claim else None

        return None
    # items = db.relationship(
    #     'ExpenseItem',
    #     backref='claim',
    #     cascade='all, delete-orphan'
    # )
    def to_dict(self):
        return {
            "id": self.id,
            "claim_number": self.claim_number,
            "claim_type": self.claim_type,
            "requester_user_id": self.requester_user_id,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "status": self.status,  
            "date_created": self.date_created.isoformat() if self.date_created else None
        }
    
class ExpenseClaimStaffModel(db.Model):
    __tablename__ = 'expense_claim_staff'

    id = db.Column(db.Integer, primary_key=True)

    staff_user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    staff = db.relationship('UserModel', backref='expense_claim_staff')
    claim_id = db.Column(db.Integer,db.ForeignKey('expense_claims.id'),nullable=False)
    claim = db.relationship('ExpenseClaim', back_populates='staff_claim')
    
    description = db.Column(db.Text)

    expense_category_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_categories.id'),
        nullable=True
    )
    expense_category = db.relationship('ExpenseCategoryModel', backref='staff_expense_items')

    expense_subcategory_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_subcategories.id'),
        nullable=True,
    )
    expense_subcategory = db.relationship(
                            'ExpenseSubCategoryModel',
                            backref='staff_expense_items'
                        )
    expense_date = db.Column(db.Date)
    

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now()
    )
    expense_staff_items = db.relationship(
        'ExpenseStaffItemModel',
        back_populates='expense_claim_staff',
        cascade='all, delete-orphan'
    )

    # items = db.relationship(
    #     'ExpenseStaffItemModel',
    #     backref='claim',
    #     cascade='all, delete-orphan'
    # )
class ExpenseStaffItemModel(db.Model):
    __tablename__ = 'expense_staff_items'

    id = db.Column(db.Integer, primary_key=True)

    expense_claim_staff_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_claim_staff.id'),
        nullable=False
    )

    expense_claim_staff = db.relationship('ExpenseClaimStaffModel', back_populates='expense_staff_items')

    

    item_name = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(12,2), nullable=True)
    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    

class ExpenseClaimChildrenModel(db.Model):
    __tablename__ = 'expense_claim_children'

    id = db.Column(db.Integer, primary_key=True)

    expense_claim_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_claims.id'),
        nullable=False)
    
    expense_claims = db.relationship(
        "ExpenseClaim",
        back_populates="children_claim",
        
    )

    member_id = db.Column(
        db.Integer,
        db.ForeignKey('member.id'),
        nullable=True
    )
    member = db.relationship('MemberModel', backref='expense_claims')

    expense_date = db.Column(db.Date)

    project_id = db.Column(
        db.Integer, 
        db.ForeignKey('product_for_sales.id'),nullable=True
    )
    project = db.relationship('ProductForSalesModel', backref='expense_claim_children')
    
    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now()
    )

    expense_children_items = db.relationship(
            'ExpenseChildrenItemModel',
            back_populates='expense_claim_children',
            cascade='all, delete-orphan'
        )

class ExpenseChildrenItemModel(db.Model):
    __tablename__ = 'expense_children_items'

    id = db.Column(db.Integer, primary_key=True)

    expense_claim_children_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_claim_children.id'),
        nullable=True
    )

    expense_claim_children = db.relationship('ExpenseClaimChildrenModel', back_populates='expense_children_items')

    receiver_type = db.Column(db.String(30),  # employee / supplier / organization / agency
        nullable=True
    )

    receiver_id = db.Column(
        db.Integer,
        nullable=True
    )

    currency_id = db.Column(
        db.Integer,
        db.ForeignKey('currencies.id'),
        nullable=True
    )
    currency = db.relationship('CurrencyModel', backref='expense_children_items')
    pay_date = db.Column(db.Date,default=db.func.current_timestamp())
    amount = db.Column(db.Numeric(12, 2), nullable=True)
    ref_amount = db.Column(db.Numeric(12, 2))
    exchange_rate = db.Column(db.Numeric(10, 4))

    remark = db.Column(db.Text)


    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    

class ExpenseClaimFileModel(db.Model):
    __tablename__ = 'expense_claim_files'

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('expense_claims.id'))
    claim_type = db.Column(db.String(20))  # staff / children

    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())