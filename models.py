from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='BASIC')
    created_time = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, username, email, password, role="BASIC"):
        self.username = username
        self.email = generate_password_hash(email)  # 实现加密存储
        print(self.email)
        self.password = generate_password_hash(password)
        print(self.password)
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password, password)  # 验证密码
