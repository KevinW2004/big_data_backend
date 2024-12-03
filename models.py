from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

from util import encrypt_email, decrypt_email

db = SQLAlchemy()
bcrypt = Bcrypt()

db_time = datetime.now


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='BASIC')
    created_time = db.Column(db.DateTime, default=db_time)

    def __init__(self, username, email, password, role="BASIC"):
        self.username = username
        self.email = encrypt_email(email)  # 实现加密存储
        print(self.email)
        self.password = generate_password_hash(password)
        print(self.password)
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password, password)  # 验证密码

    def get_original_email(self):
        print(decrypt_email(self.email))
        return decrypt_email(self.email)


class ViewHistory(db.Model):
    __tablename__ = 'view_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    access_time = db.Column(db.DateTime, default=db_time)

    def __init__(self, user_id, title):
        self.user_id = user_id
        self.title = title
