from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from base64 import b64encode, b64decode
import os

key = os.urandom(32)  # AES-256
iv = os.urandom(16)  # 初始化向量


def encrypt_email(email: str) -> str:
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(email.encode()) + padder.finalize()
    # 使用 AES CBC 模式加密
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    # 将加密后的数据和 IV 一起编码为 base64 字符串
    return b64encode(iv + encrypted).decode()


def decrypt_email(encrypted_email: str) -> str:
    # 解码 base64 数据
    encrypted_data = b64decode(encrypted_email)
    iv = encrypted_data[:16]  # 前 16 字节是 IV
    encrypted_email_data = encrypted_data[16:]  # 剩余的就是加密后的邮箱数据
    # 使用 AES CBC 模式解密
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_email_data) + decryptor.finalize()
    # 移除补齐的内容
    unpadder = padding.PKCS7(128).unpadder()
    original_email = unpadder.update(decrypted_data) + unpadder.finalize()
    return original_email.decode()
