from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from models import db
from services import *

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Hello, World!"

# papers接口
@app.route("/papers/search", methods=["GET"])
def search_papers():
    keyword = request.args.get("keyword")
    print("开始搜索，keyword: ", keyword)
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    results = PaperService.search_papers(keyword)
    return jsonify(results), 200


@app.route("/papers/get_by_title", methods=["GET"])
def get_paper_by_title():
    title = request.args.get("title")
    print("开始获取，title: ", title)
    if not title:
        return jsonify({"error": "Title is required"}), 400
    result = PaperService.get_paper_by_title(title)
    return jsonify(result), 200


@app.route("/papers/get_by_category", methods=["GET"])
def get_papers_by_category():
    category = request.args.get("category")
    print("开始获取，category: ", category)
    if not category:
        return jsonify({"error": "Category is required"}), 400
    results = PaperService.get_papers_by_category(category)
    return jsonify(results), 200

@app.route("/papers/get_citations", methods=["GET"])
def get_citations():
    title = request.args.get("title")
    print("开始获取引用，title: ", title)
    if not title:
        return jsonify({"error": "Title is required"}), 400
    results = PaperService.get_citations(title)
    return jsonify(results), 200


if __name__ == "__main__":
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    PaperService.init()
    app.run(debug=True)
