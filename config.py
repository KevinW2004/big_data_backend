class Config:
    #换成自己的数据库连接信息
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/big_data?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = '123456'  # 用于加密 JWT 令牌的密钥
    JWT_ACCESS_TOKEN_EXPIRES = 3600*24  # 设置访问令牌的过期时间（秒），例如：1小时（3600秒）