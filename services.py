from models import db, User
import pandas as pd

class UserService:
    @staticmethod
    def create_user(username, email, password):
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user



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