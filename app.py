from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import os
import datetime
import json
import requests

from engine import *
from constants import * 
from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from forms import LoginSignupForm, StockTransactionForm, StockSearchForm, UserEditForm
from secrets import keys
from exceptions import * 


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///stocks-app'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

CURR_USER_KEY = "curr_user"

app.config['SECRET_KEY'] = keys['flask_debug']
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
connect_db(app)
db.create_all()
debug = DebugToolbarExtension(app)

#********************** USER ROUTES ******************************
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

@app.route("/")
def root():
    """Homepage."""
    if not g.user:
        return render_template("home-anon.html")

    owned_stocks = Owned_Stock.get_owned_stock_for_user(g.user.id)
  
    # if not update_user_stocks(owned_stocks):     #TOO SLOW and calls external API. Implement with AJAX and load symbols instead
    #     flash("Error updating stocks from external API")

    transactions= Transaction.query.filter(Transaction.user_id == g.user.id).all()
    users_list = User.query.order_by(User.total_asset_value).all()

    return render_template('/home.html', owned_stocks=owned_stocks, transactions=transactions, users_list=users_list)    

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

@app.route('/users/edit', methods=["GET", "POST"])
def edit_user():
    """Show edit user form and validate and authenticate submission"""
    if not g.user:
        flash("unauthorized access", "danger")
        return redirect("/")
        
    form = UserEditForm(obj=g.user)
    
    if form.validate_on_submit():

        if authenticate_user_edit(form):
            return redirect("/")
        else:
            flash("Wrong password, try again!", "danger")
            return redirect('/users/edit')
    else: 
        form.populate_obj(g.user)
        return render_template("/users/edit.html", form=form)
        

@app.route('/user/portfolio', methods=["GET", "POST"])
def show_portfolio():
    """
        Show current user's owned stocks, and value, valdiates submission 
        of buying and selling stocks
    """
    if not g.user: 
        flash("Unauthorized Access", "danger")
        return redirect('/')

    form = StockTransactionForm()

    if form.validate_on_submit():
        try:
            validate_stock_transaction_form(form)
        except InvalidFormInput as e:
            flash(str(e), "danger")
            return redirect("/")

        stock_id = form.data['stock_id']
        
        if do_transaction(form):
            flash("Transaction Successful!", "success")
        else:
            flash("Transaction Failed!", "danger")
        return redirect("/user/portfolio") 

    else:
        #stock_ids = [stock.Owned_Stock.stock_id for stock in stocks]
        #for stock_id in stock_ids:            #Calls API: Extremely slow, add AXIOS request later 
        #Stock.get_update(stock_id)

        stocks = Owned_Stock.get_owned_stock_for_user(g.user.id)
        return render_template("/users/portfolio.html",stocks=stocks, form=form)

#********************************** STOCK ROUTES ****************************************
@app.route('/stocks', methods=['GET', 'POST'])
def show_stocks():
    """Shows search bar for searching stocks by name/symbol. Validates submission."""
    if not g.user:
        flash("Unauthorized Access", "danger")
        return redirect('/')
   
    form = StockSearchForm()

    if form.validate_on_submit():
        input_val = form.data['search']

        #processes string
        symbol = input_val[input_val.rfind("(")+1:input_val.rfind(")")]

        s = Stock.query.filter(Stock.stock_symbol == symbol).one()
        
        return redirect(f'/stocks/{s.id}')

    return render_template("/stocks/index.html", form=form)

    
        
@app.route('/stocks/<int:stock_id>', methods=['GET', 'POST'])
def show_stock(stock_id):
    """Shows stock data of a particular stock. Also alows the user to buy/sell the stock"""
    if not g.user:
        return redirect('/')

    form = StockTransactionForm()
    
    if(form.validate_on_submit()):
        try:
            validate_stock_transaction_form(form)
        except InvalidFormInput as e:
            flash(str(e), "danger")
            return redirect("/")
            
        if do_transaction(form):
            flash("Transaction Successful!", "success")
        else:
            flash("Transaction Failed!", "danger")

        return redirect(f"/stocks/{stock_id}")

    else:
        stock = Stock.query.get(stock_id)
        currently_owned = Owned_Stock.get_owned_stock_for_user(g.user.id, stock_id)
        currently_owned = currently_owned[0].Owned_Stock.quantity if currently_owned else 0
        
        # if not Stock.get_update(stock_id):
        if not stock:               #WARNING CALLS EXTERNAL API, ENABLE LATER when done testing
        # data = {}
        # with open('sample.json') as json_file:         #loads sample data
        #     data = json.load(json_file)                                  
            flash("Error getting update from external API", "danger")
            return redirect("/")

        data = stock.data
        return render_template('/stocks/details.html', stock=stock, data=data, form=form, currently_owned=currently_owned)  #data will be stock.data when get_update is running

    

# *********************************** API ************************************************
@app.route('/api/stocks/<int:stock_id>')
def get_stock_json(stock_id):
    """
        Returns JSON data of a particular stock. Used in javscript Axios 
        for retrieving complete stock data
    """
    if not g.user:
        return "unauthorized access", 401

    stock = Stock.query.get(stock_id)
    return jsonify(stock.data)

@app.route('/api/stocks')
def get_stock_name_list():
    """
        Returns JSON data of a list of stock names and symbols.
        Used in the javascript Axios get request for autocompletion data.
    """
    if not g.user:
        return "unauthorized access", 401

    data = []
    stocks = Stock.query.all()
    for s in stocks:
        r = f"{s.name} ({s.stock_symbol})"
        data.append(r)
    with open('test.txt', 'w') as f:
        for item in data:
            f.write("\"%s\","  % item)
    return jsonify({"stock_names": [data]})
  
        

