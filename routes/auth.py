from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, MembershipApplication

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('posts.index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        requested_role = request.form.get('requested_role', 'reader')
        if requested_role not in ('reader', 'contributor'):
            requested_role = 'reader'

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email, is_active=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        application = MembershipApplication(user_id=user.id, requested_role=requested_role)
        db.session.add(application)
        db.session.commit()

        flash('Application submitted. Please wait for admin approval before logging in.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('posts.index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is pending admin approval.', 'warning')
                return render_template('auth/login.html')
            login_user(user)
            return redirect(request.args.get('next') or url_for('posts.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('posts.index'))
