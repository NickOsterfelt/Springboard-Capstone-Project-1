
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from flask_bcrypt import Bcrypt
from os import environ
import requests
import json

from secrets import keys

bcrypt = Bcrypt()
db = SQLAlchemy()

URL = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/get-detail"

HEADERS = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': keys["rapid_api"]
}


class Transaction(db.Model):
    """Many to many table of transactions made by users, and their associated stock"""
    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        primary_key=True
    )

    stock_id = db.Column(
        db.Integer,
        db.ForeignKey('stocks.id'),
        primary_key=True
    )

    time = db.Column(
        db.DateTime,
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    stock_value_at_time = db.Column(
        db.Float,
        nullable=False
    )

    is_purchase = db.Column(
        db.Boolean,
        nullable=False
    )


class Owned_Stock(db.Model):
    """Many to Many table of user's and the stocks that they currently own"""
    __tablename__ = "owned_stocks"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        primary_key=True
    )

    stock_id = db.Column(
        db.Integer,
        db.ForeignKey('stocks.id', ondelete='cascade'),
        primary_key=True
    )

    time = db.Column(
        db.DateTime,
        nullable=True
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    value_when_purchased = db.Column(
        db.Float,
        nullable=False
    )

    @classmethod
    def get_owned_stock_for_user(cls, user_id):
        return cls.query \
            .join(User) \
            .filter(User.id == user_id) \
            .join(Stock) \
            .filter(Stock.id == Owned_Stock.stock_id) \
            .add_columns(Stock.name) \
            .all()


class User(db.Model):
    """User in stock trading system"""
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    username = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png"
    )

    password = db.Column(
        db.Text,
        # TODO: make false and have seed file generate bcrypt passwords.
        nullable=True,
    )

    current_money = db.Column(
        db.Float,
        nullable=False,
        default=10000
    )

    total_asset_value = db.Column(
        db.Float
    )

    owned_stocks = db.relationship(  # join Owned_stocks table instead with user id to get
        "Stock",  # user owned stocks
        secondary="owned_stocks",
        primaryjoin=(id == Owned_Stock.stock_id),
        backref="owned_by"
    )

    user_transactions = db.relationship(  # TODO rewrite as Transactions @classmethod with joins.
        "Transaction",
        secondary="transactions",
        primaryjoin=(id == Transaction.user_id),
        secondaryjoin=(id == Transaction.stock_id),
        backref="bought_by"
    )


    @classmethod
    def signup(cls, username, password):
        """Sign up user.

            Hashes password and adds user to system.
            """

        hashed_pwd = bcrypt.generate_password_hash(
            password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
            current_money=10000,
            total_asset_value=10000
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Finds user with `username` and `password`.

        if it finds the user, returns that user object.

        If can't find a matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Stock(db.Model):
    """A comapnies stock that a user can purchase"""
    __tablename__ = "stocks"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    stock_symbol = db.Column(
        db.String(5),
        nullable=False,
        unique=True
    )

    name = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )
    data = db.Column(
        db.JSON,
        nullable=False,
        default={}
    )
    share_price = db.Column(
        db.Float
    )

    last_updated = db.Column(
        db.DateTime
    )

    @classmethod
    def get_update(cls, stock_id, all_data=False):
        """
            Submits a get request to the yahoo finance api hosted on rapid-api, to get updated data on the stock 
            matching the stock_id. The additional data parameter specifies whether to return an object containing 
            more information on the stock from the api. 

        """
        symbol = cls.query.get(stock_id).stock_symbol

        querystring = {"region": "US", "lang": "en", "symbol": symbol}
        res = requests.request(
            "GET", URL, headers=HEADERS, params=querystring
        )

        if res.status_code != 200:
            return False  # TODO: better error handling
        json_dict = res.json()
        price = json_dict['price']['regularMarketPrice']['raw']

        
        s = cls.query.get(stock_id)
        s.share_price = price
        s.last_updated = datetime.now()

        json_dict = clean_empty(json_dict)
        s.data=json_dict

        db.session.add(s)
        db.session.commit()

        

        
        return True

    

#
def clean_empty(d):
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)
