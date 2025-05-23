
from flask import render_template, redirect, request, url_for, flash
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from flask import Flask, current_app, request, session

from flask_dance.contrib.github import github

from flask_dance.contrib.google import make_google_blueprint, google


from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import *
from apps.product.models import *
from apps.lead.models import *

from apps.authentication.util import verify_pass
import base64

from flask_principal import Identity, identity_changed

from datetime import datetime
import uuid
from sqlalchemy import and_, func, case, asc, or_, cast, String



@blueprint.route('/')
def route_default():
    # u = UserModel.query.all()
    # print(u)
    return redirect(url_for('authentication_blueprint.login'))

# Login & Registration


@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']
        remember = False
        if 'remember' in request.form:
            if request.form['remember'] == 'remember':
                remember = True
        # Locate user
        user = UserModel.query.filter_by(username=username).first()

        # Check the password and status
        # if user and verify_pass(password, user.password) and (user.status is None or user.status == 'active'):
        if user and verify_pass(password, user.password):
            print("user name and password passed.")
            login_user(user, remember=remember)
            identity = Identity(user.id)
            identity_changed.send(current_app._get_current_object(), identity=identity)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        flash("Wrong user or password!", 'danger')
        return redirect(url_for('authentication_blueprint.login'))
        # return render_template('accounts/login.html',
        #                        msg='Wrong user or password',
        #                        form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    print("User auth success")
    return redirect(url_for('home_blueprint.index'))


# @blueprint.route('/register', methods=['GET', 'POST'])
# def register():
#     create_account_form = CreateAccountForm(request.form)
#     if 'register' in request.form:

#         username = request.form['username']
#         # email = request.form['email']

#         # Check usename exists
#         user = UserModel.query.filter_by(username=username).first()
#         if user:
#             return render_template('accounts/register.html',
#                                    msg='Username already registered',
#                                    success=False,
#                                    form=create_account_form)

#         # Check email exists
#         # user = UserModel.query.filter_by(email=email).first()
#         # if user:
#         #     return render_template('accounts/register.html',
#         #                            msg='Email already registered',
#         #                            success=False,
#         #                            form=create_account_form)

#         # else we can create the user
#         user = UserModel(**request.form)
#         db.session.add(user)
#         db.session.commit()

#         # Delete user from session
#         logout_user()

#         return render_template('accounts/register.html',
#                                msg='Account created successfully.',
#                                success=True,
#                                form=create_account_form)

#     else:
#         return render_template('accounts/register.html', form=create_account_form)
    
@blueprint.route('/register', methods=['GET', 'POST'])
def register_interest():
    ref = request.args.get('ref') 
    category = ProductCategoryModel.query.all()
    country = CountryModel.query.all()
    agencies = AgencyModel.query.filter_by(org_type='agency').order_by(AgencyModel.first_name.asc()).all()
    agencies_with_IEO = [agency.__dict__.copy() for agency in agencies]
    # agencies_with_IEO.append({
    #     'id': None,
    #     'agency_code': 'IEO',
    #     'first_name': 'IEO',
    #     'last_name': '',
    # })
    product = ProductForSalesModel.query.all()


    social_channels = [
        {"id": 1, "name": "Facebook"},
        {"id": 2, "name": "Instagram"},
        {"id": 3, "name": "YouTube"},
        {"id": 4, "name": "TikTok"},
        {"id": 5, "name": "Line"},
        {"id": 6, "name": "อื่น ๆ"},
    ]

    

    # agency = AgencyModel.query.filter(AgencyModel.status == 'active').first()
    # if session.get('waiting_user_id') and session.get('waiting_user_type') == 'user':
    #     return redirect(url_for('authentication_blueprint.waiting_approval'))
    return render_template('accounts/register_interest.html',categorys=category,countrys=country, agencys=agencies_with_IEO,product=product,social_channels=social_channels,ref=ref)

@blueprint.route('/api/get_countries_by_category/<int:category_id>')
def get_countries_by_category(category_id):
    countries = db.session.query(CountryModel).join(ProductForSalesModel)\
        .filter(ProductForSalesModel.product_category_id == category_id)\
        .distinct().all()
    return jsonify([{'id': c.id, 'name': c.name} for c in countries])

@blueprint.route('/api/get_projects/<int:category_id>/<int:country_id>')
def get_projects(category_id, country_id):
    products = ProductForSalesModel.query.filter_by(
        product_category_id=category_id,
        country_id=country_id
    ).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in products])

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))

# forgot

@blueprint.route('/reset_password', methods=['GET'])
def reset_password():
    key = request.args['key'].replace('_', '=')
    return render_template('accounts/reset_password.html', key=key)

@blueprint.route('/register/agency', methods=['GET', 'POST'])
def register_agency():
        
    # ถ้าเป็น GET ให้แสดงฟอร์ม
    return render_template('accounts/register_agency.html')

@blueprint.route('/register_agency_api', methods=['POST'])
def register_agency_api():
    data = request.form
    print("data:",data)
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not password or not confirm_password:
        print("⚠️ กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน")
        return jsonify({'status': 'error', 'message': 'กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน'}), 400

    if password != confirm_password:
        print("⚠️ รหัสผ่านไม่ตรงกัน")
        return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    if UserModel.query.filter_by(username=username).first():
        print("⚠️ Username นี้ถูกใช้งานแล้ว:", username)
        return jsonify({'status': 'error', 'message': 'Username นี้ถูกใช้งานแล้ว', "data": username }), 400

    # แฮชรหัสผ่าน
    hashed_password = hash_pass(password)

    role = RoleModel.query.filter(RoleModel.name == 'agency').first()
    if not role:
        try:
            role = RoleModel(name='agency', description='Agency role')
            db.session.add(role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Cannot create role', 'error': str(e)}), 400
    
    # สร้าง User
    user = UserModel(username=username, password=password, role_id=role.id)
    db.session.add(user)
    db.session.commit()
    
    session['waiting_user_id'] = user.id
    session['waiting_user_type'] = 'agency'

    # สร้าง Agency
    agency = AgencyModel(
        user_id=user.id,
        address=data.get('address'),
        country=data.get('country'),
        first_name=data.get('fullname'),
        last_name=data.get('lastname'),
        tel=data.get('phone'),
        email=data.get('email'),
        status='appoved',
        org_type='agency',
    )
    db.session.add(agency)
    db.session.commit()

    print('success')
    return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201
    # return redirect(url_for('authentication_blueprint.waiting_approval'))


@blueprint.route('/waiting_approval')
def waiting_approval():
    
    user_id = session.get('waiting_user_id')
    user_type = session.get('waiting_user_type')
    
    if user_type == 'user':
       return render_template('accounts/waiting_approval.html')
    else:
        if not user_id:
            return redirect(url_for(f'authentication_blueprint.register_{user_type}'))  # ไม่มี session กลับไป register

        user = UserModel.query.get(user_id)

        if not user:
            session.pop('waiting_user_id', None)
            return redirect(url_for(f'authentication_blueprint.register_{user_type} '))

        # ถ้าถูก approve แล้ว → redirect ไป login
        if user.status == 'active':
            session.pop('waiting_user_id', None)  # ล้าง session
            return redirect(url_for('authentication_blueprint.login'))
    
    return render_template('accounts/waiting_approval.html')

@blueprint.route('/check_user_status', methods=['GET'])
def check_user_status():
    user_id = session.get('waiting_user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'No session'}), 401

    user = UserModel.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    return jsonify({'status': 'success', 'user_status': user.status})


@blueprint.route('/login1')
def login1():
    return render_template('accounts/login1.html')

@blueprint.route('/register/university', methods=['GET', 'POST'])
def register_university():
    
    # else:
    return render_template('accounts/register_university.html' )

@blueprint.route('/register_university_api', methods=['POST'])
def register_university_api():
    data = request.form
    print("data:",data)
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not password or not confirm_password:
        print("⚠️ กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน")
        return jsonify({'status': 'error', 'message': 'กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน'}), 400

    if password != confirm_password:
        print("⚠️ รหัสผ่านไม่ตรงกัน")
        return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    if UserModel.query.filter_by(username=username).first():
        print("⚠️ Username นี้ถูกใช้งานแล้ว:", username)
        return jsonify({'status': 'error', 'message': 'Username นี้ถูกใช้งานแล้ว', "data": username }), 400

    # แฮชรหัสผ่าน
    hashed_password = hash_pass(password)

    role = RoleModel.query.filter_by(name='university').first()

# ถ้า role ยังไม่มีในฐานข้อมูล ให้สร้างใหม่
    if not role:
        try:
            role = RoleModel(name='university', description='University role')
            db.session.add(role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Cannot create role', 'error': str(e)}), 400
    # สร้าง User
    user = UserModel(username=username, password=password, role_id=role.id,description='University role')
    db.session.add(user)
    db.session.commit()

    session['waiting_user_id'] = user.id
    session['waiting_user_type'] = 'university'
    
    nameCompany = AgencyModel.query.filter_by(company_name_th=data.get('name_univer')).first()
    
    if nameCompany :
        print("⚠️ ชื่อมหาวิทยาลัยนี้ถูกใช้งานแล้ว")
        return jsonify({'status': 'error', 'message': 'ชื่อมหาวิทยาลัยนี้ถูกใช้งานแล้ว'}), 400
    # สร้าง Agency
    university = AgencyModel(
        user_id=user.id,
        address=data.get('address'),
        country=data.get('country'),
        first_name=data.get('fullname'),
        last_name=data.get('lastname'),
        tel=data.get('phone'),
        email=data.get('email'),
        status='appoved',
        org_type='university',
        company_name_th=data.get('name_univer'),
        
        
    )
    db.session.add(university)
    db.session.commit()

    print('success')
    return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201


@blueprint.route('/register_api', methods=['POST'])
def register_api():
    ref_code = request.args.get('ref') or request.form.get('referral_code')
    print(f"➡️ ได้ ref_code: {ref_code}")
    ref_agency = None

    if ref_code:
        ref_agency = AgencyModel.query.filter_by(agency_code=ref_code).first()


    if not ref_agency:
        # ถ้าไม่เจอรหัสที่ส่งมา หรือ ref_code ไม่มี → default เป็นของ IEO
        ref_agency = AgencyModel.query.filter_by(agency_code='IEO').first()
        
    referred_by_id = ref_agency.user_id if ref_agency else None
    print(f"➡️ referred_by_id: {referred_by_id}")
    
    data = request.form
    print("data:",data)
    # username = data.get('username')
    # password = data.get('password')
    # confirm_password = data.get('confirm_password')

    # if not password or not confirm_password:
    #     print("⚠️ กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน")
    #     return jsonify({'status': 'error', 'message': 'กรุณากรอกรหัสผ่านและยืนยันรหัสผ่าน'}), 400

    # if password != confirm_password:
    #     print("⚠️ รหัสผ่านไม่ตรงกัน")
    #     return jsonify({'status': 'error', 'message': 'รหัสผ่านไม่ตรงกัน'}), 400

    # if UserModel.query.filter_by(username=username).first():
    #     print("⚠️ Username นี้ถูกใช้งานแล้ว:", username)
    #     return jsonify({'status': 'error', 'message': 'Username นี้ถูกใช้งานแล้ว', "data": username }), 400

    # แฮชรหัสผ่าน
    # hashed_password = hash_pass(password)

    # role = RoleModel.query.filter(RoleModel.name == 'agency').first()
    # if not role:
    #     try:
    #         role = RoleModel(name='agency', description='Agency role')
    #         db.session.add(role)
    #         db.session.commit()
    #     except Exception as e:
    #         db.session.rollback()
    #         return jsonify({'success': False, 'message': 'Cannot create role', 'error': str(e)}), 400
    
    # # สร้าง User
    # user = UserModel(username=username, password=password, role_id=role.id)
    # db.session.add(user)
    # db.session.commit()
    birth_date_raw = data.get('birth_date')

    if birth_date_raw:
        try:
            birth_date_str = birth_date_raw.replace('/', '-')
            birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y")
        except ValueError:
            birth_date = None
    else:
        birth_date = None

    # เตรียมข้อมูล
    agency_id = data.get('agency_id')
    agency_id = int(agency_id) if agency_id not in [None, '', 'None'] else None

    print("Raw agency_id:", data.get('agency_id'))
    print("Final agency_id:", agency_id)

    email = data.get('email')
    tel = data.get('phone')
    product_id = data.get('project')
    product = ProductForSalesModel.query.filter_by(id=product_id).first()

    first_name = data.get('fullname')
    last_name = data.get('lastname')
    gender = data.get('gender')
    line_id = data.get('line_id')
    nick_name = data.get('nickname')
    category_id = data.get('category')
    country_id = data.get('country')
    social = data.get('social')
    remask = data.get('remask')

    # เช็คว่า lead มีอยู่หรือยัง
    lead = leadModel.query.filter(
        or_(
            leadModel.email == email,
            leadModel.tel == tel
        )
    ).first()

    if not lead:
        lead = leadModel(
            first_name=first_name,
            last_name=last_name,
            tel=tel,
            email=email,
            status='new',
            gender=gender,
            line_id=line_id,
            birth_date=birth_date,
            nick_name=nick_name,
            category_id=category_id,
            country_id=country_id,
            agency_id=referred_by_id,
            product_id=product_id,
            social=social,
            remask=remask
        )
        db.session.add(lead)
        db.session.flush()  # ให้ DB สร้าง lead.id ก่อน
    else:
        # อัปเดตข้อมูล lead เดิม
        lead.first_name = first_name
        lead.last_name = last_name
        lead.nick_name = nick_name
        lead.tel = tel
        lead.email = email
        lead.gender = gender
        lead.line_id = line_id
        lead.birth_date = birth_date
        lead.agency_id = agency_id
        lead.category_id = category_id
        lead.country_id = country_id
        lead.product_id = product_id
        lead.social = social
        lead.remask = remask

    db.session.commit()

    # # สร้างหรืออัปเดต LeadProgram
    # lead_program = LeadProgram.query.filter_by(lead_id=lead.id).first()
    # if lead_program:
    #     lead_program.product_id = product.id
    #     lead_program.agency_id = agency_id
    #     lead_program.status = 'pending'
    #     lead_program.remask = remask
    # else:
    lead_program = LeadProgram(
            lead_id=lead.id,
            product_id=product.id,
            agency_id=agency_id,
            status='new',
            remask=remask
        )
    db.session.add(lead_program)

    db.session.commit()

    # เก็บ session
    session['waiting_user_id'] = lead.id
    session['waiting_user_type'] = 'user'

    return jsonify({'status': 'success', 'message': 'ลงทะเบียนสำเร็จ รอการอนุมัติจากแอดมิน'}), 201


# @login_manager.unauthorized_handler
# def unauthorized_handler():
#     return render_template('home/page-403.html'), 403


# @blueprint.errorhandler(403)
# def access_forbidden(error):
#     return render_template('home/page-403.html'), 403


# @blueprint.errorhandler(404)
# def not_found_error(error):
#     return render_template('home/page-404.html'), 404


# @blueprint.errorhandler(500)
# def internal_error(error):
#     return render_template('home/page-500.html'), 500

