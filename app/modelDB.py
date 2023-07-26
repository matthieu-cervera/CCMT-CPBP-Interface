from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt
import subprocess

'''
modelDB
    This is where the flask sqlaclhemy database tables are configured.
'''
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True)
    hashed_password = db.Column(db.String(128))
    email = db.Column(db.String(200), unique=True, index=True)
    is_valid = db.Column(db.Boolean, default=False)
    midiFilesList = db.Column(db.String(255), default="")


    def __repr__(self):
        return '<User{}>'.format(self.username)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __init__(self, username, mail):
        self.username = username
        self.email = mail


    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            u_id = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(u_id)


@login.user_loader
def load_user(u_id):
    return User.query.get(int(u_id))


class Music_sample(db.Model):

    id_sample = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    AIgenerated = db.Column(db.Boolean, nullable=False)
    user = db.Column(db.String(127), default="admin")
    answers_correct = db.Column(db.Integer, default=0)
    answers_incorrect = db.Column(db.Integer, default=0)
    beam_search = db.Column(db.Boolean)

    def __repr__(self):
        return '<Music_Sample {}>'.format(self.path)

    def __init__(self, path, AIgenerated, beam_search):
        self.path = path
        self.AIgenerated = AIgenerated
        self.beam_search = beam_search

