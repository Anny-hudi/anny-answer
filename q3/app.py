"""
用户登录系统 - 简化版主应用
层次分明的单文件结构
"""
import os
from datetime import timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, User, LoginLog
from auth import auth_bp, login_required, get_current_user, is_logged_in
from werkzeug.security import generate_password_hash, check_password_hash


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users_dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 注册主路由
    register_main_routes(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册CLI命令
    register_cli_commands(app)
    
    return app


def register_main_routes(app):
    """注册主要路由"""
    
    @app.route('/')
    def index():
        """首页"""
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
        
        return render_template('dashboard.html', user=user)
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """仪表板"""
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
        
        # 获取用户登录历史
        login_logs = LoginLog.query.filter_by(user_id=user.id)\
                                 .order_by(LoginLog.login_time.desc())\
                                 .limit(10).all()
        
        return render_template('dashboard.html', 
                             user=user,
                             login_logs=login_logs)
    
    @app.route('/profile')
    @login_required
    def profile():
        """用户资料"""
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
        
        # 获取登录历史
        login_logs = LoginLog.query.filter_by(user_id=user.id)\
                                 .order_by(LoginLog.login_time.desc())\
                                 .limit(10).all()
        
        return render_template('profile.html', 
                             user=user,
                             login_logs=login_logs)
    
    # API路由
    @app.route('/api/register', methods=['POST'])
    def api_register():
        """API注册接口"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': '无效的JSON数据'}), 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            # 基本验证
            if not username or not email or not password:
                return jsonify({'success': False, 'message': '所有字段都是必填的'}), 400
            
            if len(username) < 3:
                return jsonify({'success': False, 'message': '用户名至少需要3个字符'}), 400
            
            if len(password) < 6:
                return jsonify({'success': False, 'message': '密码至少需要6个字符'}), 400
            
            # 检查用户是否已存在
            if User.query.filter_by(username=username).first():
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': '邮箱已存在'}), 400
            
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """API登录接口"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': '无效的JSON数据'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            # 基本验证
            if not username or not password:
                return jsonify({'success': False, 'message': '用户名和密码都是必填的'}), 400
            
            # 验证用户
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            # 设置会话
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
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500
    
    @app.route('/api/logout', methods=['POST'])
    def api_logout():
        """API登出接口"""
        try:
            if 'user_id' in session and 'login_log_id' in session:
                # 更新登出时间
                login_log = LoginLog.query.get(session['login_log_id'])
                if login_log:
                    login_log.logout_time = datetime.utcnow()
                    db.session.commit()
            
            session.clear()
            return jsonify({'success': True, 'message': '登出成功'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'登出失败: {str(e)}'}), 500
    
    @app.route('/api/status', methods=['GET'])
    def api_status():
        """API认证状态检查"""
        try:
            if is_logged_in():
                user = get_current_user()
                if user:
                    return jsonify({
                        'authenticated': True,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email
                        }
                    })
            
            return jsonify({'authenticated': False}), 401
            
        except Exception as e:
            return jsonify({'error': f'状态检查失败: {str(e)}'}), 500


def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Page not found'}), 404
        return render_template('error.html', error='页面未找到'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('error.html', error='服务器内部错误'), 500
    
    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('auth.login'))


def register_cli_commands(app):
    """注册CLI命令"""
    @app.cli.command()
    def init_db():
        """初始化数据库"""
        db.create_all()
        print('数据库初始化完成')
    
    @app.cli.command()
    def reset_db():
        """重置数据库"""
        db.drop_all()
        db.create_all()
        print('数据库重置完成')


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
    
    # 运行应用
    app.run(debug=True, port=5001)