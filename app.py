from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from models import db, bcrypt
import pymysql
from services import *

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello():
    return 'Hello, World!'


@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    # 如果用户名已经存在，会返回400
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    print("username:", username)
    print("password:", password)
    results = UserService.create_user(username, email, password)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    results = UserService.login(username, password)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


@app.route('/user', methods=['GET'])
@jwt_required()
def get_user_info():
    current_user = get_jwt_identity()
    results = UserService.get_user(current_user)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


@app.route('/user/upgrade', methods=['GET'])
@jwt_required()
def upgrade():
    current_user = get_jwt_identity()
    results = UserService.upgrade(current_user)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


@app.route('/papers/search', methods=['GET'])
@jwt_required()
def search_papers():
    keyword = request.args.get('keyword')
    print("开始搜索，keyword: ", keyword)
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    results = PaperService.search_papers(keyword)
    return jsonify(results), 200


@app.route('/papers/get_by_title', methods=['GET'])
@jwt_required()
def get_paper_by_title():
    title = request.args.get('title')
    print("开始获取，title: ", title)
    if not title:
        return jsonify({"error": "Title is required"}), 400
    result = PaperService.get_paper_by_title(title)
    return jsonify(result), 200


@app.route('/papers/get_by_category', methods=['GET'])
@jwt_required()
def get_papers_by_category():
    category = request.args.get('category')
    print("开始获取，category: ", category)
    if not category:
        return jsonify({"error": "Category is required"}), 400
    results = PaperService.get_papers_by_category(category)
    return jsonify(results), 200


@app.route("/papers/get_citations", methods=["GET"])
@jwt_required()
def get_citations():
    # VIP专属
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if user.role == "BASIC":
        return jsonify({"error": "此为VIP专属功能，请升级VIP后使用"}), 201
    title = request.args.get("title")
    print("开始获取引用，title: ", title)
    if not title:
        return jsonify({"error": "Title is required"}), 400
    results = PaperService.get_citations(title)
    return jsonify(results), 200


@app.route('/papers/get_similar', methods=['GET'])
@jwt_required()
def get_similar_papers():
    # VIP专属
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if user.role == "BASIC":
        return jsonify({"error": "此为VIP专属功能，请升级VIP后使用"}), 201
    title = request.args.get('title')
    print("开始获取相似，title: ", title)
    if not title:
        return jsonify({"error": "Title is required"}), 400
    results = PaperService.get_similar_papers(title, k=10)
    return jsonify(results), 200


@app.route('/paper/addRecord', methods=['POST'])
@jwt_required()
# 接收一个参数：title
def update_history():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    user_id = user.id
    print(user_id)
    title = request.args.get("title")
    results = PaperService.add_record(title, user_id)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


@app.route('/paper/getHistory', methods=['GET'])
@jwt_required()
# 无需任何参数
def get_history():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    user_id = user.id
    results = PaperService.get_paper_history(user_id)
    if results.get('code') == 200:
        return jsonify(results), 200
    else:
        return jsonify(results), 400


if __name__ == '__main__':
    app.config.from_object(Config)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    with app.app_context():
        db.create_all()
    PaperService.init()
    app.run(debug=True)
