
from flask import render_template, redirect, request, url_for, flash
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from flask import Flask, current_app, request, session

from flask_dance.contrib.github import github

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import *

from apps.authentication.util import verify_pass
import base64

from flask_principal import Identity, identity_changed

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

        # Check the password
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


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        # email = request.form['email']

        # Check usename exists
        user = UserModel.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        # user = UserModel.query.filter_by(email=email).first()
        # if user:
        #     return render_template('accounts/register.html',
        #                            msg='Email already registered',
        #                            success=False,
        #                            form=create_account_form)

        # else we can create the user
        user = UserModel(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template('accounts/register.html',
                               msg='Account created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))

# forgot

@blueprint.route('/reset_password', methods=['GET'])
def reset_password():
    key = request.args['key'].replace('_', '=')
    return render_template('accounts/reset_password.html', key=key)


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

