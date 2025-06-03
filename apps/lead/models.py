from flask_login import UserMixin

from sqlalchemy.orm import relationship

from apps import db, login_manager

from apps.authentication.util import hash_pass

from flask import jsonify

from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey

    
@dataclass
class leadModel(db.Model):
    __tablename__ = 'lead'

    id : int
    agency_id:int
    product_id:int
    first_name:str
    last_name:str
    nick_name:str
    tel:str
    email:str
    gender:str
    line_id:str
    remask:str
    social:str
    birth_date:str

    id = db.Column(db.Integer, primary_key=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    first_nameEN = db.Column(db.String(100))
    last_nameEN = db.Column(db.String(100))
    year = db.Column(db.String(), nullable=True,server_default='2025')
    nick_name = db.Column(db.String(100))
    tel = db.Column(db.String(30))
    email = db.Column(db.String(100))
    status = db.Column(db.String(20))  # New, Contacted, Converted, Dropped
    gender = db.Column(db.String(20))  # pending / approved / rejected
    line_id = db.Column(db.String(20))  # pending / approved / rejected
    remask = db.Column(db.String(250))  # New, Contacted, Converted, Dropped
    social = db.Column(db.String(250))  # New, Contacted, Converted, Dropped
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    birth_date = db.Column(db.DateTime,  default=None)
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    
    agency_id = db.Column(db.Integer, db.ForeignKey('agency.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id", ondelete="CASCADE"), nullable=True )
    product_id = db.Column(db.Integer, db.ForeignKey("product_for_sales.id", ondelete="CASCADE"), nullable=True )
    
    category = db.relationship("ProductCategoryModel", back_populates="lead", lazy=True)
    country = db.relationship("CountryModel", back_populates="lead", lazy=True)
    product = db.relationship("ProductForSalesModel", back_populates="lead", lazy=True)
    agency = db.relationship("AgencyModel", back_populates="lead", lazy=True)
    orders = db.relationship("OrderModel", back_populates="lead", lazy=True)

    lead_product_links = db.relationship("LeadProgram", back_populates="lead", overlaps="products,leads")
    products = db.relationship("ProductForSalesModel", secondary="lead_program", back_populates="leads", overlaps="lead_product_links")



@dataclass
class LeadProgram(db.Model):
    __tablename__ = 'lead_program'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id', ondelete='CASCADE'))
    product_id = db.Column(db.Integer, db.ForeignKey('product_for_sales.id'))
    created_at = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    status = db.Column(db.String(20))  # New, Contacted, Converted, Dropped
    remask = db.Column(db.String(250))
    year = db.Column(db.String(), nullable=True)

    agency_id = db.Column(db.Integer, db.ForeignKey('agency.id', ondelete='CASCADE'), nullable=True)
    agency = db.relationship("AgencyModel", back_populates="lead_programs", overlaps="products,agency")
    lead = db.relationship("leadModel", back_populates="lead_product_links", overlaps="products,leads")
    product = db.relationship("ProductForSalesModel", backref="lead_product_links", overlaps="products,leads")