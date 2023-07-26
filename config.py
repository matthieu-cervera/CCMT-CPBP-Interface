import os


'''
CONFIG
    This is where the flask sqlaclhemy database is configured.
'''
class Config:
    # Randomly generated secret key to secure the session
    SECRET_KEY = 'YFwZonIEKERodjmsek97SAZY_LT6AXam'

    base_dir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
