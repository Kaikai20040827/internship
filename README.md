<!-- NOTE: 本文件已调整为“每句中文后接对应英语”的格式；内容来自原 README，未改变实质信息。 -->

# 保密文件箱（Secure File Box）
# Secure File Box (保密文件箱)

Secure File Box 是一个基于 Flask 的简单 Web 应用，用于安全地加密、存储和管理用户文件。
Secure File Box is a simple Flask-based web app for securely encrypting, storing, and managing user files.

它使用人脸识别作为第二因子进行登录（用户名 + 密码 + 人脸验证），并在服务器端以加密形式保存文件。
It uses face recognition as a second factor for login (username + password + face verification) and stores files encrypted on the server.

---

## 功能一览 / Features
## 🚀 Features / 功能一览

- 用户注册（用户名、密码 + 人脸照片）。 / User registration (username, password + face photo).

- 登录使用用户名 + 密码 + 人脸识别。 / Login using username + password + face recognition.

- 上传文件（文件在数据库中以对称加密保存）。 / Upload files (files are symmetrically encrypted in the database).

- 下载、删除文件（均记录操作日志）。 / Download and delete files (operations are logged).

- 操作记录页面（查看上传/下载/删除历史）。 / Activity log page (view upload/download/delete history).

- 使用 `Flask-Login`, `SQLAlchemy`, `face_recognition`, `cryptography.fernet`。 / Uses `Flask-Login`, `SQLAlchemy`, `face_recognition`, `cryptography.fernet`.

---

## 技术栈 / Technology Stack
## 🧭 Technology Stack / 技术栈

- Python 3.13。 / Python 3.13.

- Flask。 / Flask.

- Flask-Login。 / Flask-Login.

- Flask-SQLAlchemy。 / Flask-SQLAlchemy.

- MySQL (mysql-connector-python)。 / MySQL (mysql-connector-python).

- face_recognition（依赖 dlib & OpenCV）。 / face_recognition (depends on dlib & OpenCV).

- cryptography（Fernet 对称加密）。 / cryptography (Fernet symmetric encryption).

---

## 重要提示 / Important Notes
## ⚠️ Important Notes / 重要提示

- 当前示例代码包含开发/演示用途的配置。 / The example code currently contains development/demo configurations.

  - 默认会在应用启动时执行 `db.drop_all()` -> `db.create_all()`（会清空数据库），仅用于开发，**请在生产中移除**。 / The app by default runs `db.drop_all()` -> `db.create_all()` on startup (which clears the database); this is for development only — remove it in production.

  - `SECRET_KEY`、数据库连接 URI、Fernet 密钥均在代码中或以示例形式暴露。请使用环境变量或配置文件管理这些秘密。 / `SECRET_KEY`, database connection URI, and Fernet key are exposed in code/examples; use environment variables or config files to manage secrets.

  - 密码以明文形式存储（`User.password`），请在生产环境使用安全的密码哈希（如 bcrypt 或 werkzeug.security 系列）。 / Passwords are stored in plaintext (`User.password`) — use a secure password hash in production (e.g., bcrypt or werkzeug.security).

  - 当前 `Fernet` 密钥在每次应用启动时随机生成，若不使用持久密钥已上传的文件将无法解密。请在安全配置中设置并保持不变（或使用 KMS）。 / The Fernet key is generated randomly on each app start; without a persistent key uploaded files cannot be decrypted. Use a persistent key (or KMS).

---

## 安装依赖 / Install Requirements
##⚠️📦 Install Requirements / 安装依赖

- 依赖列在 `secureFileBox/requirement.txt`。 / Dependencies are listed in `secureFileBox/requirement.txt`.

- 主要依赖：flask, flask-login, flask-sqlalchemy, flask-mysqldb, face-recognition, numpy, cryptography, python-dotenv, werkzeug, mysql-connector-python。 / Key dependencies: flask, flask-login, flask-sqlalchemy, flask-mysqldb, face-recognition, numpy, cryptography, python-dotenv, werkzeug, mysql-connector-python.

注：`face_recognition` 与 `dlib`/OpenCV 的安装在某些系统（尤其 Windows）上较为复杂；建议使用 `conda` 并从 `conda-forge` 安装 `dlib`、`cmake`。 / Note: Installing `face_recognition` (and dlib/OpenCV) can be complex on some systems (especially Windows); it's recommended to use `conda` and install `dlib`, `cmake` from `conda-forge`.

示例（也可以不创建新环境，使用 base）： / Example (you may also use the base env instead of creating a new one):

```powershell
conda create -n securefilebox python=3.13
conda activate securefilebox
conda install -c conda-forge dlib cmake numpy
pip install -r secureFileBox/requirement.txt
```

---

## 配置 / Configuration
## ⚠️🔧 Configuration / 配置

⚠️ In `app.py` 的第 14 行中，把 password 改成自己的数据库密码。 / ⚠️ In `app.py` line 14, change the password to your database password.

示例： / Example:

```
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/secure_file_box'
```

如何生成 Fernet key： / How to generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将生成的 `.env` 中的 `FERNET_KEY` 填入。也可以使用云 KMS 或 OS 密钥库保护该密钥。 / Put the generated key into `.env` as `FERNET_KEY`. You may also use cloud KMS or OS key stores to protect the key.

---

## 数据库初始化 / Database Setup
## 🏁 Database Setup / 数据库初始化

1. 安装并运行 MySQL。 / 1. Install and run MySQL.

2. 使用 MySQL 客户端创建数据库： / 2. Use a MySQL client to create the database:

```sql
CREATE DATABASE secure_file_box CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'a-secure-password';
GRANT ALL PRIVILEGES ON secure_file_box.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

3. 更新 `.env` 中 `DATABASE_URI` 使用上面的 `app_user` 和密码。 / 3. Update `DATABASE_URI` in `.env` with the `app_user` and password above.

4. 应用启动会自动创建模型中的表（开发模式）。生产中请使用迁移工具（例如 Alembic 或 Flask-Migrate）。 / 4. The app will auto-create model tables at startup (development mode). Use migration tools (Alembic/Flask-Migrate) in production.

---

## 运行（开发） / Run the App (Development)
## ▶️ Run the App (Development) / 运行（开发）

1. 激活 Python 环境并安装包（参见上文）。 / 1. Activate the Python environment and install packages (see above).

2. 复制并编辑 `.env`，设置 `SECRET_KEY`, `DATABASE_URI`, `FERNET_KEY`。 / 2. Copy and edit `.env`, set `SECRET_KEY`, `DATABASE_URI`, `FERNET_KEY`.

3. 本地运行（确保已配置 MySQL 并创建数据库）： / 3. Run locally (ensure MySQL and the database are configured):

```powershell
cd secureFileBox
python app.py
```

4. 打开浏览器访问 http://127.0.0.1:5000/。 / 4. Open a browser and visit http://127.0.0.1:5000/.

注：仓库中还包含 `register.py`，它包含部分重复实现，主入口请使用 `app.py`。 / Note: The repo also includes `register.py` with overlapping logic; use `app.py` as the main entry.

---

## 使用说明 / Usage Guide
## 📝 Usage Guide / 简要使用说明

1. 打开主页 -> 到注册页面 -> 注册用户名、设置密码并上传一张清晰的人脸照片（用于登录认证）。 / 1. Open the homepage -> go to Register -> create a username, password and upload a clear face photo (for authentication).

2. 登录时需要用户名、密码以及一张清晰的人脸照片进行比对。 / 2. Login requires username, password and a clear face photo for matching.

3. 登录后可将文件上传（会在数据库中以加密形式存储）；可下载或删除文件并查看操作日志。 / 3. After login you can upload files (stored encrypted in the DB); download or delete files and view operation logs.

---

## 安全建议 / Security Considerations
## 🔐 Security Considerations / 安全建议

- 永远不要在源码内硬编码敏感值（密码、数据库连接、密钥）。应使用环境变量或 Vault 等秘密管理方案。 / - Never hard-code secrets (passwords, DB URIs, keys) in source; use env vars or a secrets manager.

- 切勿在生产中启用自动 `db.drop_all()`。改用数据库迁移工具（`flask-migrate` / `alembic`）。 / - Do not enable automatic `db.drop_all()` in production — use DB migrations (`flask-migrate` / `alembic`).

- 密码必须以安全哈希存储（bcrypt / scrypt / passlib / werkzeug.security.generate_password_hash）。 / - Store passwords with secure hashing (bcrypt / scrypt / passlib / werkzeug.security.generate_password_hash).

- 持久化 Fernet 密钥（或使用 KMS），否则重启后无法解密已保存文件。 / - Persist the Fernet key (or use KMS), otherwise uploaded files cannot be decrypted after restart.

- 在生产部署中启用 HTTPS，设置 secure cookie 和 HTTPOnly 标志以保护会话。 / - Use HTTPS in production and set secure and HTTPOnly flags on cookies.

- 考虑对上传文件进行类型验证、反恶意内容过滤与病毒扫描。 / - Consider file type validation, malware filtering and virus scanning for uploads.

- 记录日志时避免泄露敏感信息。遵循最小权限原则配置数据库账号。 / - Avoid leaking sensitive info in logs. Follow least-privilege for DB accounts.

---

## 项目结构 / Project Structure
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

## 开发说明 / Development Notes
## 🛠️ Development Notes / 开发说明

- `face_recognition` 在 Windows 系统上安装可能较为复杂，应预先安装 dlib 与 CMake。 / - Installing `face_recognition` on Windows can be complex; pre-install `dlib` and CMake.

- 若要替代 Face recognition 的本地实现，可以考虑通过外部服务（如第三方人脸识别 API）或使用纯密码 + 2FA（例如 TOTP）实现。 / - To replace local face recognition, consider external face-recognition services or use password + 2FA (e.g., TOTP).

- 为了文件更高效的存储和管理，可以把加密文件替换为将密文保存到磁盘并在 DB 中保存路径。此外，推荐将文件分割为块，并使用 S3 或其他对象存储来节省数据库资源。 / - For more efficient storage, save ciphertext to disk and store paths in DB, or chunk files and use S3/object storage to reduce DB usage.

---

## 贡献 / Contributing
## 🤝 Contributing / 贡献

欢迎任何形式的贡献：Bug 报告、建议、PR 等。 / Contributions welcome: bug reports, suggestions, PRs.

请在提交 PR 前： / Before submitting a PR:

1. Fork 仓库并创建特性分支。 / 1. Fork the repo and create a feature branch.

2. 提交清晰描述的更改与注释。 / 2. Submit clear changes and comments.

3. 推荐添加单元/集成测试（如果适用）。 / 3. Prefer adding unit/integration tests where applicable.

---

<!-- 文件结束 -->
