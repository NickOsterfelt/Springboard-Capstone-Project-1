from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from os import environ
import datetime
import json

from flask import request
import requests

from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from forms import LoginSignupForm, StockTransactionForm, StockSearchForm, StockTransactionPorfolioForm
from secrets import keys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///stocks-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

CURR_USER_KEY = "curr_user"

app.config['SECRET_KEY'] = keys['flask_debug']
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

#********************** USER ROUTES ******************************
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        g.user = None
        del session[CURR_USER_KEY]
    #else:
        #exception
    

@app.route("/")
def root():
    """Homepage."""
    if g.user:
        owned_stocks = g.user.owned_stocks

        
        return render_template('/home.html', owned_stocks = owned_stocks )
        
    else:
        return render_template("home-anon.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    """Show signup form and validate submission"""

    form = LoginSignupForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,   
            )
        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template('users/signup')
        db.session.commit()
        do_login(user)
        return redirect("/")
    else:
        return render_template('/users/signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Show login form and validate submission"""

    form = LoginSignupForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}, login successful!", "success")
            return redirect('/')

        flash("Invalid username/password combonation", "danger")
        return redirect('/login')

    return render_template('users/login.html', form = form)

@app.route('/logout')
def logout():
    """Do Logout"""
    if g.user:
        flash("See you later! Logout Successful.", "success")
        do_logout()
    
    return redirect('/')

# @app.route('/users/edit')
# def edit_user():
#     if g.user:
#         form = 
#     else:
#         flash("unauthorized access", "danger")

@app.route('/user/portfolio', methods=["GET", "POST"])
def show_portfolio():
    if g.user: 
        form = StockTransactionPorfolioForm()
        transaction_type = form.transaction_type.data
        amount = form.amount.data
        
        if form.validate_on_submit():

            if len(form.data['stock_id']) > 10:
                raise Exception()               # malicious code handling?
            stock_id = form.data['stock_id']
            try: 
                stock_id = int(stock_id)
            except ValueError:
                return redirect("/")
            
            if transaction_type == "buy":
                if g.user.buy_stock(amount, stock_id):
                    flash("Transaction Successful!", "success")
                else:
                    flash("Transaction Failed!", "danger")
            if transaction_type == "sell":
                if g.user.sell_stock(amount, stock_id):
                    flash("Transaction Successful!", "success")
                else:
                    flash("Transaction Failed!", "danger")
            
            return redirect("/user/portfolio") 
        else:
            owned_stocks = Owned_Stock.get_owned_stock_for_user(g.user.id)
            return render_template("/users/portfolio.html",stocks=owned_stocks, form=form)
    else:
        flash("Unauthorized Access", "danger")
        return redirect('/')

#********************************** STOCK ROUTES ****************************************
@app.route('/stocks', methods=['GET', 'POST'])
def show_stocks():
    if g.user:

        form = StockSearchForm()

        if form.validate_on_submit():
            input_val = form.search._value()
            symbol = input_val[input_val.find("(")+1:input_val.find(")")]
            
            s = Stock.query.filter(Stock.stock_symbol == symbol).one()
            
            return redirect(f'/stocks/{s.id}')
            #return redirect(f"/stocks/{stock_id}")

        
        return render_template("/stocks/index.html", form=form)

    return redirect('/')
        
@app.route('/stocks/<int:stock_id>', methods=['GET', 'POST'])
def show_stock(stock_id):
    if g.user:

        form = StockTransactionForm()
        
        if(form.validate_on_submit()):
            amount = form.amount.data
            transaction_type = form.transaction_type.data
            stock= Stock.query.get(stock_id)
            value = stock.share_price
            if transaction_type == "buy":
                
                if g.user.buy_stock(amount, stock_id):
                    flash("Transaction Successful!", "success")
                else:
                    flash("Transaction Failed!", "danger")
            if transaction_type == "sell":
                if g.user.sell_stock(amount, stock_id):
                    flash("Transaction Successful!", "success")
                else:
                    flash("Transaction Failed!", "danger")
        
            return redirect(f"/stocks/{stock_id}")

        else:
            stock = Stock.query.get(stock_id)
            currently_owned = Owned_Stock.get_owned_stock_for_user(g.user.id)
            currently_owned = currently_owned[0].Owned_Stock.quantity if currently_owned else 0
            if not Stock.get_update(stock_id, True):      #WARNING CALLS EXTERNAL API, ENABLE LATER when done testing
            # data = {}
            # with open('sample.json') as json_file:         #loads sample data
            #     data = json.load(json_file)                                  
                flash("Error getting update from external API", "danger")
                return redirect("/")

            data = stock.data
            return render_template('/stocks/details.html', stock=stock, data=data, form=form, currently_owned=currently_owned)  #data will be stock.data when get_update is running

    return redirect('/')

# *********************************** API ************************************************
@app.route('/api/stocks/<int:stock_id>')
def get_stock_json(stock_id):
    if g.user:
        stock = Stock.query.get(stock_id)
        return jsonify(stock.data)
    else:
        return "unauthorized access", 401

@app.route('/api/stocks')
def get_stock_name_list():
    data = []
    if g.user:
        stocks = Stock.query.all()
        for s in stocks:
            r = f"{s.name} ({s.stock_symbol})"
            data.append(r)
        with open('test.txt', 'w') as f:
            for item in data:
                f.write("\"%s\","  % item)
        return jsonify({"stock_names": [data]})
    else:
        return "unauthorized access", 401

