from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from __init__ import db  # Import from __init__.py
from models import User  # Use absolute import

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            # ✅ Redirect to change password if required
            if user.must_change_password:
                return redirect(url_for('auth.change_password'))
            
            return redirect(url_for('main.dashboard'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('auth.change_password'))

        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.must_change_password = False  # Remove forced password change
        db.session.commit()

        flash('Password changed successfully. Please log in again.')
        return redirect(url_for('auth.logout'))

    return render_template('change_password.html')
