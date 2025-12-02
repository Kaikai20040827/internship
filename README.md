<!--- NOTE: This README is bilingual (中文/English) to support both local and international contributors. --->

# Secure File Box (保密文件箱)

Secure File Box（保密文件箱）是一个基于 Flask 的简单 Web 应用，用于安全地加密、存储和管理用户文件。它使用人脸识别作为第二因子进行登录（用户名 + 密码 + 人脸验证），并在服务器端以加密形式保存文件。

---

## 🚀 Features / 功能一览
- 用户注册（用户名、密码 + 人脸照片）
- 登录使用用户名 + 密码 + 人脸识别
- 上传文件（文件在数据库中以对称加密保存）
- 下载、删除文件（均记录操作日志）
- 操作记录页面（查看上传/下载/删除历史）
- 使用 `Flask-Login`, `SQLAlchemy`, `face_recognition`, `cryptography.fernet`

---

## 🧭 Technology Stack / 技术栈
- Python 3.13
- Flask
- Flask-Login
- Flask-SQLAlchemy
- MySQL (mysql-connector-python)
- face_recognition (依赖 dlib & OpenCV)
- cryptography (Fernet 对称加密)

---

## ⚠️ Important Notes / 重要提示
- 当前示例代码包含开发/演示用途的配置：
  - 默认会在应用启动时执行 `db.drop_all()` -> `db.create_all()`（会清空数据库），仅用于开发，**请在生产中移除**。
  - `SECRET_KEY`, 数据库连接 URI, Fernet 密钥均在代码中或以示例形式暴露。请使用环境变量或配置文件管理这些秘密。
  - 密码以明文形式存储（`User.password`），请在生产环境使用安全的密码哈希（如 bcrypt 或 werkzeug.security 系列）。
  - 当前 `Fernet` 密钥在每次应用启动时随机生成，若不使用持久密钥已上传的文件将无法解密。请在安全配置中设置并保持不变（或使用 KMS）。

---

##⚠️📦 Install Requirements / 安装依赖
⚠️⚠️⚠️依赖列在 `secureFileBox/requirement.txt`⚠️⚠️⚠️：

- flask
- flask-login
- flask-sqlalchemy
- flask-mysqldb
- face-recognition
- numpy
- cryptography
- python-dotenv
- werkzeug
- mysql-connector-python

注：`face_recognition` 与 `dlib`/OpenCV 的安装在某些系统（尤其 Windows）上较为复杂；建议使用 `conda` 并从 `conda-forge` 安装 `dlib`、`cmake`。例如：
(也可以不创建新环境，使用base)

```powershell
conda create -n securefilebox python=3.13
conda activate securefilebox
conda install -c conda-forge dlib cmake numpy
pip install -r secureFileBox/requirement.txt
```

---

## ⚠️🔧 Configuration / 配置
⚠️⚠️⚠️app.py的第14行中，把password改成自己的数据库密码⚠️⚠️⚠️:
```
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/secure_file_box'
```

如何生成 Fernet key：
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将生成的 `.env` 中的 `FERNET_KEY` 填入。也可以使用云 KMS 或 OS 密钥库保护该密钥。

---

## 🏁 Database Setup / 数据库初始化
1. 安装并运行 MySQL。
2. 使用 MySQL 客户端创建数据库：

```sql
CREATE DATABASE secure_file_box CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'a-secure-password';
GRANT ALL PRIVILEGES ON secure_file_box.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

3. 更新 `.env` 中 `DATABASE_URI` 使用上面的 `app_user` 和密码。
4. 应用启动会自动创建模型中的表（开发模式）。生产中请使用迁移工具（例如 Alembic 或 Flask-Migrate）。

---

## ▶️ Run the App (Development) / 运行（开发）
1. 激活 Python 环境并安装包（参见上文）。
2. 复制并编辑 `.env`，设置 `SECRET_KEY`, `DATABASE_URI`, `FERNET_KEY`。
3. 本地运行（确保已配置 MySQL 并创建数据库）：

```powershell
cd secureFileBox
python app.py
```

4. 打开浏览器访问 http://127.0.0.1:5000/。

注：仓库中还包含 `register.py`，它包含部分重复实现，主入口请使用 `app.py`。

---

## 📝 Usage Guide / 简要使用说明
1. 打开主页 -> 到注册页面 -> 注册用户名、设置密码并上传一张清晰的人脸照片（用于登录认证）。
2. 登录时需要用户名、密码以及一张清晰的人脸照片进行比对。
3. 登录后可将文件上传（会在数据库中以加密形式存储）；可下载或删除文件并查看操作日志。

---

## 🔐 Security Considerations / 安全建议
- 永远不要在源码内硬编码敏感值（密码、数据库连接、密钥）。应使用环境变量或 Vault 等秘密管理方案。
- 切勿在生产中启用自动 `db.drop_all()`。改用数据库迁移工具（`flask-migrate` / `alembic`）。
- 密码必须以安全哈希存储（bcrypt / scrypt / passlib / werkzeug.security.generate_password_hash）。
- 持久化 Fernet 密钥（或使用 KMS），否则重启后无法解密已保存文件。
- 在生产部署中启用 HTTPS，设置 secure cookie 和 HTTPOnly 标志以保护会话。
- 考虑对上传文件进行类型验证、反恶意内容过滤与病毒扫描。
- 记录日志时避免泄露敏感信息。遵循最小权限原则配置数据库账号。

---

## 📁 Project Structure / 项目结构
```
secureFileBox/
├─ app.py                # 主程序入口（路由、数据库模型、业务逻辑）
├─ register.py           # 注册逻辑（和 app.py 有部分重复）
├─ requirement.txt       # 依赖列表
├─ templates/            # Jinja2 前端模板
├─ static/               # CSS/JS 等静态资源
├─ uploads/              # 上传文件目录（本地用于持久化样例）
├─ file/                 # 示例文档
├─ photo/                # 示例人脸照片
```

---

## 🛠️ Development Notes / 开发说明
- `face_recognition` 在 Windows 系统上安装可能较复杂，应预先安装 dlib 与 CMake。
- 若要替代 Face recognition 的本地实现，可以考虑通过外部服务（如第三方人脸识别 API）或使用纯密码 + 2FA（例如 TOTP）实现。
- 为了文件更高效的存储和管理，可以把加密文件替换为将密文保存到磁盘并在 DB 中保存路径。此外，推荐将文件分割为块，并使用 S3 或其他对象存储来节省数据库资源。

---

## 🤝 Contributing / 贡献
欢迎任何形式的贡献：Bug 报告、建议、PR 等。请在提交 PR 前：
1. Fork 仓库并创建特性分支。
2. 提交清晰描述的更改与注释。
3. 推荐添加单元/集成测试（如果适用）。

---



