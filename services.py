from models import db, User, bcrypt
import pandas as pd
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


class UserService:
    @staticmethod
    def create_user(username, email, password):
        if User.query.filter_by(username=username).first():
            print(User.query.filter_by(username=username).first().username)
            return {'msg': 'username already exists', 'code': 400}
        user = User(username=username, email=email, password=password)

        db.session.add(user)
        db.session.commit()
        return {'msg': "success", 'code': 200}

    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username).first()
        print("check password")
        if user.check_password(password):
            access_token = create_access_token(identity=username)
            return {'access_token': access_token, 'code': 200}
        else:
            return {'msg': 'wrong password', 'code': 400}

    @staticmethod
    def get_user(username):
        user = User.query.filter_by(username=username).first()
        if user:
            return {'username': username, 'role': user.role, 'code': 200}
        else:
            return {'msg': 'User not found', 'code': 400}

    @staticmethod
    def upgrade(username):
        user = User.query.filter_by(username=username).first()
        if user.role != 'VIP':
            user.role = 'VIP'
            db.session.commit()
            return {'msg': 'successfully upgrade', 'code': 200}
        else:
            return {'msg': 'Already', 'code': 400}


class PaperService:
    dataset_path = './dataset/papers.csv'
    papers = pd.read_csv(dataset_path)

    @staticmethod
    def search_papers(keyword):
        # 根据标题搜索论文
        results = PaperService.papers[PaperService.papers['title'].str.contains(keyword, case=False, na=False)]
        return results.to_dict(orient='records')

    @staticmethod
    def get_paper_by_title(title):
        # 根据标题获取论文, 这里仅仅获取第一条
        result = PaperService.papers[PaperService.papers['title'] == title]
        return result.to_dict(orient='records')[0]

    @staticmethod
    def get_paper_by_category(category):
        # 根据类别获取论文
        results = PaperService.papers[PaperService.papers['category'] == category]
        return results.to_dict(orient='records')
