from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from decimal import Decimal


@dataclass
class ProductCategoryModel(db.Model):
    __tablename__ = "product_category"
    
    id: int
    name: str     
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)  
    products = db.relationship("ProductForSalesModel", backref="category", cascade="all, delete")
    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    # interested_users = db.relationship("interestedUsersModel", back_populates="category", lazy=True)
    lead = db.relationship("leadModel", back_populates="category", lazy=True)


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            
        }

@dataclass
class CountryModel(db.Model):
    __tablename__ = "country"
    
    id: int
    name: str     
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)  
    products = db.relationship("ProductForSalesModel", backref="country", cascade="all, delete" )
    supplier = db.relationship("SupplierModel", backref="country", cascade="all, delete" )
    employee = db.relationship("EmployeeModel", backref="country", cascade="all, delete" )
    organizations = db.relationship("OrganizationModel", backref="country", cascade="all, delete" )
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    # interested_users = db.relationship("interestedUsersModel", back_populates="country", lazy=True)
    lead = db.relationship("leadModel", back_populates="country", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            
        }
        
@dataclass
class PeriodModel(db.Model):
    __tablename__ = "period"
    
    id: int
    name: str     
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)  
    products = db.relationship("ProductForSalesModel", backref="period", cascade="all, delete" )
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            
        }
        
@dataclass
class term_of_paymentModel(db.Model):
    __tablename__ = "term_of_payment"
    
    id: int
    name: str     
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)  
    products = db.relationship("ProductForSalesModel", backref="term_of_payment", cascade="all, delete" )
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            
        }
        
@dataclass
class ProductForSalesModel(db.Model):        
    __tablename__ = "product_for_sales"
    
    id: int
    product_category_id: int
    period_id: int
    term_of_payment_id: int
    country_id: int
    name: str   
    year: str   
    status: str   
    # detail : str
    price: float  # ✅ เพิ่มฟิลด์ price 
    images: str

    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)  
    year = db.Column(db.String(), nullable=False)  
    price = db.Column(db.Float, nullable=False)  # ✅ เพิ่ม price ลงในฐานข้อมูล
    product_category_id = db.Column(db.Integer, db.ForeignKey("product_category.id", ondelete="CASCADE"), nullable=True )
    country_id = db.Column(db.Integer, db.ForeignKey("country.id", ondelete="CASCADE"), nullable=True )
    period_id = db.Column(db.Integer, db.ForeignKey("period.id", ondelete='CASCADE'), nullable=True )
    term_of_payment_id = db.Column(db.Integer, db.ForeignKey("term_of_payment.id", ondelete='CASCADE'), nullable=True )
    
    images = db.relationship("MD_Image", back_populates="product", cascade="all, delete", lazy=True)
    files = db.relationship("FileModel", back_populates="product", cascade="all, delete", lazy=True)
    installments= db.relationship("installmentsPaymentModel", back_populates="product", cascade="all, delete", lazy=True)
    # interested_users = db.relationship("interestedUsersModel", back_populates="product", lazy=True)
    lead = db.relationship("leadModel", back_populates="product", lazy=True)
    orders = db.relationship("OrderModel", back_populates="product", lazy=True)
    payments = db.relationship("PaymentModel", back_populates="product", cascade="all, delete", lazy=True)
    order_items = db.relationship("OrderItemModel", back_populates="product",lazy=True)
    
    leads = db.relationship("leadModel", secondary="lead_program", back_populates="products", overlaps="lead_product_links")

    detail = db.Column(db.Text(),default=None)
    start_at = db.Column(db.DateTime,  default=None)
    end_at = db.Column(db.DateTime,  default=None)

    status = db.Column(db.String(20), default="pending",nullable=True)  # pending, approved, rejected

    
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
@dataclass
class FileModel(db.Model):
    __tablename__ = 'files'
    id :int
    product_for_sales_id :int

    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), default=False)  # ชื่อไฟล์
    filepath = db.Column(db.String(512), default=False)  # พาธของไฟล์
    file_type  = db.Column(db.Integer, comment='1:PS')
    product_for_sales_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product = db.relationship("ProductForSalesModel", back_populates="files")  # ✅ back_populates ที่ถูกต้อง
    flag_delete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    
@dataclass
class MD_Image(db.Model):
    __tablename__ = "md_image"
    
    id: int
    product_for_sales_id: int
    image: str
    
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text)
    
    product_for_sales_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product = db.relationship("ProductForSalesModel", back_populates="images")  # ✅ ใช้ชื่อ relationship ที่ถูกต้อง
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    

@dataclass
class installmentsPaymentModel(db.Model):
    __tablename__ = "installments_payment"
    
    id: int
    price: int
    term_detail: str
    amount: str
    year:str
    check_vat: bool
    
    id = db.Column(db.Integer, primary_key=True)
    term_detail = db.Column(db.String(), nullable=False)
    amount = db.Column(db.String(), nullable=False)
    year = db.Column(db.String(), nullable=True,server_default='2025') 
    price = db.Column(Numeric(precision=12, scale=2), nullable=False, server_default='0.00')
    product_for_sales_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"))
    product = db.relationship("ProductForSalesModel", back_populates="installments")
    check_vat = db.Column(db.Boolean, default=False, comment="1:vat, 2:no vat")

    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    