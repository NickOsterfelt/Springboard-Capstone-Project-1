
from flask import Flask
from secrets import keys
import os

def setup_app_config():

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///stocks-app'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True

    CURR_USER_KEY = "curr_user"

    app.config['SECRET_KEY'] = keys['flask_debug']
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    return app

