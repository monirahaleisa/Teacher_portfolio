from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from src.data_helpers import get_user_by_username, get_user_by_id

# User class for Flask-Login
class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return self.id
    
    def check_password(self, password):
        user_data = get_user_by_username(self.username)
        if user_data:
            return check_password_hash(user_data['password'], password)
        return False
    
    @staticmethod
    def get(user_id):
        user_data = get_user_by_id(user_id)
        if user_data:
            return User(user_data['id'], user_data['username'])
        return None

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = get_user_by_username(username)
        
        if user_data:
            if check_password_hash(user_data['password'], password):
                user = User(user_data['id'], user_data['username'])
                login_user(user)
                flash('تم تسجيل الدخول بنجاح', 'success')
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('admin.dashboard'))
            else:
                flash('كلمة المرور غير صحيحة', 'error')
        else:
            flash('اسم المستخدم غير موجود', 'error')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))
