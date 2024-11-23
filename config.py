class Config:
    #换成自己的数据库连接信息
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123qweASD@localhost/big_data?charset=utf8' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False