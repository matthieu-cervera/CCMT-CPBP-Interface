from flask import Flask
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config


'''
INIT
    Initialize the flask app
'''
app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view='homepage_not_logged'

from app import modelDB, views


# To re-create the whole database, or to creat new tables, uncomment this
# with app.app_context():
#     db.create_all()
