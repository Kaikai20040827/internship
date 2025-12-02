from flask import Flask, render_template, redirect, url_for, request, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import face_recognition
import numpy as np
import os
from cryptography.fernet import Fernet
from urllib.parse import quote

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 生产环境需替换为随机密钥
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/secure_file_box'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB文件限制

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库和登录管理器
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 生成加密密钥
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# -------------------------- 数据库模型 --------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # 生产环境需用hashlib加密存储
    face_encoding = db.Column(db.LargeBinary, nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)
    operations = db.relationship('OperationLog', backref='user', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    encrypted_data = db.Column(db.LargeBinary, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    operations = db.relationship(
        'OperationLog', 
        backref='file', 
        lazy=True,
        cascade="all, save-update, merge, delete-orphan",
        passive_deletes=True 
    )

class OperationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    operation_type = db.Column(db.String(20), nullable=False)  # 'upload', 'download', 'delete'
    operation_time = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.String(500))  # 存储文件删除前的名称，避免丢失信息

# -------------------------- 登录加载函数 --------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------- 路由（删除逻辑优化） --------------------------
@app.route('/')
def home():
    # Redirect to the dedicated login route to keep methods consistent
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        face_image = request.files['face_image']
        
        # 检查用户名是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        # 处理人脸图像
        if face_image:
            img = face_recognition.load_image_file(face_image)
            face_encodings = face_recognition.face_encodings(img)
            if not face_encodings:
                flash('无法识别人脸，请上传清晰照片')
                return redirect(url_for('register'))
            
            # 创建用户（生产环境需加密密码：如hashlib.sha256(password.encode()).hexdigest()）
            new_user = User(
                username=username,
                password=password,
                face_encoding=face_encodings[0].tobytes()
            )
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        face_image = request.files['face_image']
        
        # 验证用户和密码
        user = User.query.filter_by(username=username).first()
        if not user or user.password != password:  # 生产环境需用hash验证
            flash('用户名或密码错误')
            return redirect(url_for('login'))
        
        # 验证人脸
        if face_image:
            img = face_recognition.load_image_file(face_image)
            face_encodings = face_recognition.face_encodings(img)
            if not face_encodings:
                flash('无法识别人脸，请上传清晰照片')
                return redirect(url_for('login'))
            
            # 对比人脸特征
            stored_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)
            if face_recognition.compare_faces([stored_encoding], face_encodings[0])[0]:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('人脸验证失败')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功登出')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # 获取当前用户文件，按上传时间倒序
    files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return render_template('dashboard.html', files=files)

@app.route('/operation-logs')
@login_required
def operation_logs():
    # 获取当前用户操作记录，按时间倒序
    logs = OperationLog.query.filter_by(user_id=current_user.id).order_by(OperationLog.operation_time.desc()).all()
    return render_template('operation_logs.html', logs=logs)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('没有文件部分')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件')
        return redirect(url_for('dashboard'))
    
    if file:
        try:
            # 加密文件并保存到数据库
            file_data = file.read()
            encrypted_data = cipher_suite.encrypt(file_data)
            new_file = File(
                filename=file.filename,
                encrypted_data=encrypted_data,
                user_id=current_user.id
            )
            db.session.add(new_file)
            db.session.commit()
            
            # 记录上传操作
            log = OperationLog(
                user_id=current_user.id,
                file_id=new_file.id,
                operation_type='upload',
                details=f'上传文件：{file.filename}'
            )
            db.session.add(log)
            db.session.commit()
            flash('文件已上传并加密')
        except Exception as e:
            flash(f'上传失败：{str(e)}')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('无权访问此文件')
        return redirect(url_for('dashboard'))
    
    try:
        # 解密文件并生成下载响应
        decrypted_data = cipher_suite.decrypt(file.encrypted_data)
        response = make_response(decrypted_data)
        
        # 处理中文文件名编码
        filename_encoded = quote(file.filename)
        response.headers.set(
            'Content-Disposition',
            f'attachment; filename="{filename_encoded}"; filename*=UTF-8\'\'{filename_encoded}'
        )
        
        # 记录下载操作
        log = OperationLog(
            user_id=current_user.id,
            file_id=file.id,
            operation_type='download',
            details=f'下载文件：{file.filename}'
        )
        db.session.add(log)
        db.session.commit()
        return response
    except Exception as e:
        flash(f'下载失败：{str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('无权访问此文件')
        return redirect(url_for('dashboard'))
    
    try:
        log = OperationLog(
            user_id=current_user.id,
            file_id=file.id,
            operation_type='delete',
            details=f'删除文件：{file.filename}'
        )
        db.session.add(log)
        
        db.session.delete(file)
        db.session.commit()
        flash('文件已删除')
    except Exception as e:
        flash(f'删除失败：{str(e)}')
    return redirect(url_for('dashboard'))

with app.app_context():
    db.drop_all()  
    db.create_all() 

# 运行应用
if __name__ == '__main__':
    app.run(debug=True)  
