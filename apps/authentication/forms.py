# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import Email, DataRequired

# login and registration


class LoginForm(FlaskForm):
    username = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username',
                         id='username_create',
                         validators=[DataRequired()])
    email = StringField('Email',
                      id='email_create',
                      validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[DataRequired()])
    
    
class CreateAgencyForm(FlaskForm):
    # User Information
    username = StringField('Username', id='usernames',validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
    # Agency Information
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    currency = StringField('Currency', validators=[DataRequired()])
    tel = StringField('Telephone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact_person = StringField('Contact Person', validators=[DataRequired()])
    
    # Submit
    # submit = SubmitField('Register')    
