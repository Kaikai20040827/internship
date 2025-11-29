from flask import Flask, render_template, redirect, url_for, request, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import face_recognition
import numpy as np
import os
from cryptography.fernet import Fernet
from urllib.parse import quote

# 初始化Flask应用实例
app = Flask(__name__)
# 设置应用密钥，用于会话安全（生产环境需替换为随机密钥）
app.config['SECRET_KEY'] = 'your-secret-key-here'
# 配置MySQL数据库连接URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:123456@localhost/secure_file_box'
# 关闭SQLAlchemy修改跟踪警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 设置文件上传目录
app.config['UPLOAD_FOLDER'] = 'uploads'
# 设置最大文件上传大小为10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# 确保上传目录存在，如果不存在则创建
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化SQLAlchemy数据库实例
db = SQLAlchemy(app)
# 初始化Flask-Login管理器
login_manager = LoginManager(app)
# 设置登录视图，未登录用户会被重定向到此
login_manager.login_view = 'login'

# 生成Fernet加密密钥
key = Fernet.generate_key()
# 创建加密套件实例
cipher_suite = Fernet(key)


# -------------------------- 数据库模型定义 --------------------------
# 用户模型，继承UserMixin提供Flask-Login所需方法
class User(UserMixin, db.Model):
    # 用户ID，主键
    id = db.Column(db.Integer, primary_key=True)
    # 用户名，唯一且不能为空
    username = db.Column(db.String(50), unique=True, nullable=False)
    # 密码（生产环境需用hashlib加密存储）
    password = db.Column(db.String(100), nullable=False)
    # 人脸编码数据，二进制大对象
    face_encoding = db.Column(db.LargeBinary, nullable=False)
    # 与File模型的一对多关系
    files = db.relationship('File', backref='owner', lazy=True)
    # 与操作日志的一对多关系
    operations = db.relationship('OperationLog', backref='user', lazy=True)


# 文件模型
class File(db.Model):
    # 文件ID，主键
    id = db.Column(db.Integer, primary_key=True)
    # 文件名
    filename = db.Column(db.String(200), nullable=False)
    # 加密后的文件数据
    encrypted_data = db.Column(db.LargeBinary, nullable=False)
    # 外键，关联用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 文件上传时间，默认为当前时间
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 与操作日志的一对多关系，设置级联删除
    operations = db.relationship(
        'OperationLog',
        backref='file',
        lazy=True,
        cascade="all, save-update, merge, delete-orphan",
        passive_deletes=True
    )


# 操作日志模型
class OperationLog(db.Model):
    # 日志ID，主键
    id = db.Column(db.Integer, primary_key=True)
    # 外键，关联用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 外键，关联文件ID（可为空，因为文件删除后日志仍需保留）
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    # 操作类型：上传、下载、删除
    operation_type = db.Column(db.String(20), nullable=False)
    # 操作时间，默认为当前时间
    operation_time = db.Column(db.DateTime, default=datetime.utcnow)
    # 操作详情，如文件删除前的名称
    details = db.Column(db.String(500))


# -------------------------- 用户加载回调函数 --------------------------
# Flask-Login要求的用户加载函数
@login_manager.user_loader
def load_user(user_id):
    # 根据用户ID从数据库加载用户
    return User.query.get(int(user_id))


# -------------------------- 路由定义 --------------------------
# 根路由，显示首页（登录页）
@app.route('/')
def home():
    # 渲染登录模板
    return render_template('login.html')


# 用户注册路由，支持GET和POST方法
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 如果是POST请求，处理注册表单提交
    if request.method == 'POST':
        # 从表单获取用户名
        username = request.form['username']
        # 从表单获取密码
        password = request.form['password']
        # 从表单获取人脸图像文件
        face_image = request.files['face_image']

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            # 如果用户名存在，显示错误消息
            flash('用户名已存在')
            # 重定向回注册页面
            return redirect(url_for('register'))

        # 检查是否上传了人脸图像
        if face_image:
            # 使用face_recognition加载图像文件
            img = face_recognition.load_image_file(face_image)
            # 提取人脸编码特征
            face_encodings = face_recognition.face_encodings(img)
            # 检查是否成功识别人脸
            if not face_encodings:
                # 如果无法识别人脸，显示错误消息
                flash('无法识别人脸，请上传清晰照片')
                # 重定向回注册页面
                return redirect(url_for('register'))

            # 创建新用户实例
            new_user = User(
                username=username,  # 设置用户名
                password=password,  # 设置密码（生产环境需加密）
                # 将人脸编码转换为字节存储
                face_encoding=face_encodings[0].tobytes()
            )
            # 添加用户到数据库会话
            db.session.add(new_user)
            # 提交数据库事务
            db.session.commit()
            # 显示成功消息
            flash('注册成功，请登录')
            # 重定向到登录页面
            return redirect(url_for('login'))
    # 如果是GET请求，渲染注册模板
    return render_template('register.html')



# 在应用上下文中操作数据库
with app.app_context():
    # 删除所有已存在的表（危险操作，仅用于开发）
    db.drop_all()
    # 创建所有定义的表
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
    # 运行Flask应用，启用调试模式
