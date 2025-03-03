from flask import Flask
from models import db, init_db
from routes import app as routes_app

app = Flask(__name__)

app.config.from_object('config.Config')

db.init_app(app)

@app.before_request
def create_tables():
    init_db(app)

app.register_blueprint(routes_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)  