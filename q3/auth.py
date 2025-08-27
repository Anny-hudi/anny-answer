"""认证相关功能模块"""
from flask import Blueprint, request, session, flash, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, LoginLog

auth_bp = Blueprint('auth', __name__)

def is_logged_in():
    """检查用户是否已登录"""
    return 'user_id' in session

def get_current_user():
    """获取当前登录用户"""
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

def login_required(f):
    """装饰器：要求用户登录"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已存在')
            return render_template('register.html')
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            
            # 记录登录日志
            login_log = LoginLog(
                user_id=user.id,
                ip_address=request.remote_addr
            )
            db.session.add(login_log)
            db.session.commit()
            
            session['login_log_id'] = login_log.id
            
            flash('登录成功')
            return redirect(url_for('main.dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """用户登出"""
    if 'user_id' in session and 'login_log_id' in session:
        # 更新登出时间
        login_log = LoginLog.query.get(session['login_log_id'])
        if login_log:
            login_log.logout_time = datetime.utcnow()
            db.session.commit()
    
    session.clear()
    flash('已登出')
    return redirect(url_for('auth.login'))
