
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
    """Many to many table of transactions made by users, and the associated stock in the transaction"""
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

    stock_symbol = db.Column(
        db.String(5),
        nullable=False,
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

    @classmethod
    def get_user_transactions(cls, user_id):
        return cls.query \
            .join(User) \
            .filter(User.id == user_id) \
            .join(Stock) \
            .filter(Stock.id == Transaction.stock_id) \
            .add_columns(Stock.name, Stock.stock_symbol, Stock.share_price) \
            .all()

    @classmethod
    def generate_transaction(cls, user, stock, amount, is_buy):
        """Adds a transaction"""
        t = Transaction()

        t.user_id = user.id
        t.stock_id = stock.id
        t.stock_symbol = stock.stock_symbol
        t.is_purchase = True if is_buy else False
        t.quantity = amount
        t.stock_value_at_time = stock.share_price
        t.time = datetime.now()

        db.session.add(t)
        

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
    def user_owns_stock(cls, user_id, stock_id):
        """Returns the owned_stock or false if a given user owns a given stock"""
        owned_stock = cls.query.filter(cls.user_id == user_id).filter(cls.stock_id == stock_id).all()
        if owned_stock:
            return owned_stock[0]
        else:
            return False

    @classmethod
    def add_owned_stock_for_user(cls, user, stock, amount):
        """ Adds to existing owned_stock, or creates a new entry"""
        owned_stock = Owned_Stock.user_owns_stock(user.id, stock.id)

        if owned_stock:         #stock is already owned, then add to quanity and update value/time.
            owned_stock.quantity += amount
            owned_stock.value_when_purchased = stock.share_price
            owned_stock.time = datetime.now()
        else:                   #create a new owned stock entry
            owned_stock = Owned_Stock()
            owned_stock.user_id = user.id
            owned_stock.stock_id = stock.id
            owned_stock.quantity = amount
            owned_stock.value_when_purchased = stock.share_price
            owned_stock.time = datetime.now()

        db.session.add(owned_stock)

    @classmethod
    def remove_owned_stock_for_user(cls, user, stock, amount):
        """removes owned_stock. If amount is greater than currently owned quantity, then all will be removed"""
        owned_stock = Owned_Stock.user_owns_stock(user.id, stock.id)
        if owned_stock:             
            if amount >= owned_stock.quantity:
                db.session.delete(owned_stock)
            else:
                owned_stock.quantity -= amount
                db.session.add(owned_stock)                

    @classmethod
    def get_owned_stock_for_user(cls, user_id, stock_id=0):
        """gets stocks that are owned by users. returns owned_stock objects"""
        if stock_id != 0:
            return cls.query \
            .join(User) \
            .filter(User.id == user_id) \
            .join(Stock) \
            .filter(Stock.id == stock_id) \
            .add_columns(Stock.name, Stock.stock_symbol, Stock.share_price) \
            .all()

        return cls.query \
            .join(User) \
            .filter(User.id == user_id) \
            .join(Stock) \
            .filter(Stock.id == Owned_Stock.stock_id) \
            .add_columns(Stock.name, Stock.stock_symbol, Stock.share_price) \
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
        nullable=False,
    )

    current_money = db.Column(
        db.Float,
        nullable=False,
        default=10000
    )

    total_asset_value = db.Column(
        db.Float,
        default=0
    )

    user_transactions = db.relationship(  # TODO rewrite as Transactions @classmethod with joins.
        "Transaction",
        secondary="transactions",
        primaryjoin=(id == Transaction.user_id),
        secondaryjoin=(id == Transaction.stock_id),
        backref="bought_by"
    )
    
    def buy_stock(self, amount, stock_id):
        """Buy a stock"""
        stock = Stock.query.get(stock_id)

        if self.current_money < (amount * stock.share_price):
            return False                                        #TODO: make exception instead
        else:
            Transaction.generate_transaction(self, stock, amount, True)
            Owned_Stock.add_owned_stock_for_user(self, stock, amount)
            self.current_money -= (amount * stock.share_price)
            self.update_asset_value()

            db.session.add(self)
        
            db.session.commit()
            return True
    
    def sell_stock(self, amount, stock_id):
        """"Sells a stock that the user owns."""
        stock = Stock.query.get(stock_id)
        owned_stock = Owned_Stock.user_owns_stock(self.id, stock_id)

        if owned_stock:
            if amount > owned_stock.quantity:   #prevents negative stocks
                amount = owned_stock.quantity 
            
            Transaction.generate_transaction(self, stock, amount, False)
            Owned_Stock.remove_owned_stock_for_user(self, stock, amount)
            self.current_money += (amount * stock.share_price)
            self.update_asset_value()

            db.session.add(self)
        
            db.session.commit()
            return True
        else:
            return False            #TODO: make exceptions instead

    def update_asset_value(self):
        """
            Sums the value of each stock owned by the user, multiplied by
            the number of each respective stock that the user owns. 
            The value is stored as User.total_asset_value
        """
        stocks = Owned_Stock.get_owned_stock_for_user(self.id)
        dir(stocks)
        val = 0
        for stock in stocks:
            val += (stock.Owned_Stock.quantity * stock.share_price)
        
        self.total_asset_value = val

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
    def get_update(cls, stock_id):
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

def clean_empty(d):
    """Removes empty entries (entries that evaluate to false) in a dictionary object"""
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}

def connect_db(app):
    """Connect to database."""
    db.app = app
    db.init_app(app)
