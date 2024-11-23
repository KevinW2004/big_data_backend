from flask import Flask
from config import Config
from models import db

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'


if __name__ == '__main__':
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    


