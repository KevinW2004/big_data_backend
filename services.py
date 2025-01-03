from models import db, User, bcrypt, ViewHistory
import pandas as pd
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

import json
import os
import numpy as np
import faiss


class UserService:
    @staticmethod
    def create_user(username, email, password):
        if User.query.filter_by(username=username).first():
            print(User.query.filter_by(username=username).first().username)
            return {"msg": "username already exists", "code": 400}
        user = User(username=username, email=email, password=password)
        user.get_original_email()
        db.session.add(user)
        db.session.commit()
        return {"msg": "success", "code": 200}

    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username).first()
        print("check password")
        if user.check_password(password):
            access_token = create_access_token(identity=username)
            return {"access_token": access_token, "code": 200}
        else:
            return {"msg": "wrong password", "code": 400}

    @staticmethod
    def get_user(username):
        user = User.query.filter_by(username=username).first()
        if user:
            return {"username": username, "role": user.role, "code": 200}
        else:
            return {"msg": "User not found", "code": 400}

    @staticmethod
    def upgrade(username):
        user = User.query.filter_by(username=username).first()
        if user.role != "VIP":
            user.role = "VIP"
            db.session.commit()
            return {"msg": "successfully upgrade", "code": 200}
        else:
            return {"msg": "Already", "code": 400}


class PaperService:
    original_dataset_path = "./dataset/papers.csv"
    dataset_path = "./dataset/papers_with_predictions.csv"
    papers = pd.read_csv(dataset_path)
    feats = pd.read_csv(
        f"./dataset/feats.csv.gz", compression="gzip", header=None
    ).values.astype(np.float32)
    category_mapping = {}
    title_to_index = {}
    citations = {}
    faiss_index = None

    @staticmethod
    def init():
        # 1. 创建分类映射
        if os.path.exists("./dataset/category_mapping.json"):
            with open("./dataset/category_mapping.json", "r") as f:
                PaperService.category_mapping = json.load(f)
        else:
            original_papers = pd.read_csv(PaperService.original_dataset_path)
            original_papers["category"] = original_papers["category"].replace(
                "Unknown", -1
            )
            original_papers["category"] = original_papers["category"].astype("category")
            PaperService.category_mapping = {
                code: category
                for category, code in zip(
                    original_papers["category"].cat.categories,
                    range(len(original_papers["category"].cat.categories)),
                )
            }
            with open("./dataset/category_mapping.json", "w") as f:
                json.dump(PaperService.category_mapping, f)
        PaperService.papers["category"] = PaperService.papers["category"].astype("string")
        PaperService.papers["category"] = PaperService.papers["category"].map(PaperService.category_mapping)
        # 2. 创建id索引
        if os.path.exists("./dataset/title_to_index.json"):
            with open("./dataset/title_to_index.json", "r") as f:
                PaperService.title_to_index = json.load(f)
        else:
            papers_df = pd.read_csv("./dataset/papers.csv")
            PaperService.title_to_index = {
                title: index for index, title in enumerate(papers_df["title"])
            }
            with open("./dataset/title_to_index.json", "w") as f:
                json.dump(PaperService.title_to_index, f)
        # 3. 获取引用关系
        edges = pd.read_csv(
            "./dataset/edges.csv.gz", compression="gzip", header=None
        ).values.T.astype(np.int32)
        citer, citee = edges
        for cite, cited in zip(citer, citee):
            if cite not in PaperService.citations:
                PaperService.citations[cite] = []
            PaperService.citations[cite].append(cited)
        # 4. 创建faiss索引
        # index = faiss.IndexFlatIP(PaperService.feats.shape[1])
        PaperService.faiss_index = faiss.IndexFlatL2(128)  # 使用 L2 距离的平面索引
        PaperService.faiss_index.add(PaperService.feats)

    @staticmethod
    def get_similar_papers(title, k=5):
        # 根据标题获取相似论文
        src_id = PaperService.title_to_index[title]
        query_vec = PaperService.feats[src_id]
        distances, indices = PaperService.faiss_index.search(
            query_vec.reshape(1, -1), k + 1
        )
        print(distances, indices)
        similar_papers = PaperService.papers.iloc[indices[0]].to_dict(orient="records")
        # 去除自身
        similar_papers = [p for p in similar_papers if p["title"] != title][:k]
        return similar_papers

    @staticmethod
    def search_papers(keyword):
        # 根据标题搜索论文
        results = PaperService.papers[
            PaperService.papers["title"].str.contains(keyword, case=False, na=False)
        ]
        return results.to_dict(orient="records")

    @staticmethod
    def get_paper_by_title(title):
        # 根据标题获取论文, 这里仅仅获取第一条
        result = PaperService.papers[PaperService.papers["title"] == title]
        return result.to_dict(orient="records")[0]

    @staticmethod
    def get_paper_by_id(id):
        # 根据索引获取论文
        result = PaperService.papers.iloc[id]
        return result.to_dict()

    @staticmethod
    def get_papers_by_category(category):
        # 根据类别获取论文
        results = PaperService.papers[PaperService.papers["category"] == category]
        return results.to_dict(orient="records")

    @staticmethod
    def get_citations(title):
        # 根据标题获取引用论文
        citer_id = PaperService.title_to_index[title]
        cited_ids = PaperService.citations.get(citer_id, [])
        cited_papers = PaperService.papers.iloc[cited_ids]
        return cited_papers.to_dict(orient="records")

    @staticmethod
    def add_record(title, user_id):
        if not title:
            return {"msg": "title is null", "code": 400}
        viewHistory = ViewHistory(user_id, title)
        db.session.add(viewHistory)
        db.session.commit()
        return {"msg": "success", "code": 200}

    @staticmethod
    def get_paper_history(user_id):
        history_records = (
            ViewHistory.query.filter_by(user_id=user_id)
            .order_by(ViewHistory.access_time.desc())
            .limit(20)
            .all()
        )
        history = [{"title": record.title} for record in history_records]
        return {"msg": history, "code": 200}

    @staticmethod
    def get_recommendations(user_id):
        history_records = (
            ViewHistory.query.filter_by(user_id=user_id)
            .order_by(ViewHistory.access_time.desc())
            .limit(10)
            .all()
        )
        history_titles = [record.title for record in history_records]
        recommend_papers = []
        if len(history_titles) == 0:  # 无历史记录，随机推荐
            recommend_papers = PaperService.papers.sample(n=10).tolist()
        else:
            for title in history_titles:
                similar_papers = PaperService.get_similar_papers(title, k=8)
                recommend_papers.extend(similar_papers)
        recommend_papers = recommend_papers
        # 去重
        unique_papers = {}
        for paper in recommend_papers:
            unique_papers[paper["title"]] = paper
        recommend_papers = list(unique_papers.values())  # 得到去重后的值
        print(recommend_papers)
        return recommend_papers
