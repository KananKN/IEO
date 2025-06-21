from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey


@dataclass
class OrderModel(db.Model):
    __tablename__ = "order"

    id: int
    note: str
    order_number: str
    payment_method: str
    status: str
    price: float

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(), nullable=False)
    order_number = db.Column(db.String(), nullable=True)
    payment_method = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(250), default='pending', comment='pending, partially_paid, paid')
    price = db.Column(db.Float, nullable=False)

    lead_id = db.Column(db.Integer, db.ForeignKey("lead.id", ondelete="CASCADE"))
    lead = db.relationship("leadModel", back_populates="orders", lazy="select")

    product_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product = db.relationship("ProductForSalesModel", back_populates="orders")

    member_id = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="CASCADE"))
    member = db.relationship("MemberModel", back_populates="orders", lazy="select")

    order_items = db.relationship("OrderItemModel", back_populates="order", cascade="all, delete")
    payments = db.relationship("PaymentModel", back_populates="order", cascade="all, delete", lazy=True)

    agency_id = db.Column(db.Integer, db.ForeignKey('agency.id', ondelete='CASCADE'), nullable=True)
    agency = db.relationship("AgencyModel", back_populates="orders")
    year = db.Column(db.String(), nullable=True)

    total_price = db.Column(db.Numeric(precision=10, scale=2), nullable=True)  # ราคารวมก่อนส่วนลด
    discount = db.Column(db.Numeric(precision=10, scale=2), default=0.00)  # ส่วนลดทั้งหมด
    net_price = db.Column(db.Numeric(precision=10, scale=2), nullable=True)

    terms = db.relationship('OrderTermModel', backref='order', lazy='dynamic')

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


@dataclass
class OrderItemModel(db.Model):
    __tablename__ = "order_items"

    id: int
    order_id: int
    product_id: int

    id = db.Column(db.Integer, primary_key=True)
    unit_price = db.Column(db.Float, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"))
    product_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product_name = db.Column(db.String(), nullable=True)
    order_number = db.Column(db.String(), nullable=True)

    order = db.relationship("OrderModel", back_populates="order_items")
    product = db.relationship("ProductForSalesModel", back_populates="order_items")
    note = db.Column(db.String()) 
    

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    
@dataclass
class MemberModel(db.Model):
    __tablename__ = "member"

    id = db.Column(db.Integer, primary_key=True)
    member_code = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    nick_name = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(100))
    status = db.Column(db.String(20))  # New, Contacted, Converted, Dropped
    gender = db.Column(db.String(20))  # pending / approved / rejected
    line_id = db.Column(db.String(20))  # pending / approved / rejected
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    birth_date = db.Column(db.DateTime,  default=None)
    address = db.Column(db.Text())
    first_nameEN = db.Column(db.String(100))
    last_nameEN = db.Column(db.String(100))
    year = db.Column(db.String(), nullable=True,server_default='2025')

    orders = db.relationship("OrderModel", back_populates="member", cascade="all, delete")

    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

@dataclass
class PaymentModel(db.Model):
    __tablename__ = "payments"

    id:int

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"))
    order = db.relationship("OrderModel", back_populates="payments", lazy=True)
    
    product_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product = db.relationship("ProductForSalesModel", back_populates="payments")
    amount = db.Column(db.Float, nullable=False) 

    payment_date = db.Column(db.DateTime,  default=None)
    payment_method = db.Column(db.String(250)) 
    payment_no = db.Column(db.String(250)) 
    note = db.Column(db.String(250)) 
    status = db.Column(db.String(100))  # New, Contacted, Converted, Dropped
    sequence = db.Column(db.Integer)  # งวดที่เท่าไหร่ เช่น 1, 2, 3

    files = db.relationship(
        "FilePaymentModel",
        back_populates="payment",
        primaryjoin="PaymentModel.id == foreign(FilePaymentModel.term_id)",
        lazy="joined"
    )



    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    


@dataclass
class FilePaymentModel(db.Model):
    __tablename__ = 'filesPayment'
    id :int

    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), default=False)  # ชื่อไฟล์
    filepath = db.Column(db.String(512), default=False)  # พาธของไฟล์
    file_type  = db.Column(db.Integer, comment='1:PS')

    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id", ondelete="CASCADE"))
    payment = db.relationship(
        "PaymentModel",
        back_populates="files",
        foreign_keys=[payment_id]
    )
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"))
    term_id = db.Column(db.Integer, db.ForeignKey("order_terms.id", ondelete="CASCADE"))
    
    flag_delete = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    

class OrderTermModel(db.Model):
    __tablename__ = 'order_terms'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    term_detail = db.Column(db.String(255))
    amount = db.Column(db.Numeric(precision=12, scale=2), nullable=False)
    sequence = db.Column(db.Integer)  # งวดที่เท่าไหร่ เช่น 1, 2, 3
    discount = db.Column(db.Numeric(precision=12, scale=2), nullable=False, server_default="0.00")
    net_price = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    outstanding_amount = db.Column(db.Numeric(precision=12, scale=2), nullable=True, server_default="0.00")

    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())







    
 