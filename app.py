from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import datetime
import json
import requests

from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from forms import LoginSignupForm, StockTransactionForm, StockSearchForm, StockTransactionPorfolioForm, UserEditForm
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
        owned_stocks = Owned_Stock.get_owned_stock_for_user(g.user.id)

        #updates each stock from external API, comment out when testing
        # update_success = True
        # for stock in owned_stocks:          #TODO: add loading page maybe? or AJAX requests
        #     if not Stock.get_update(stock.Owned_Stock.stock_id):
        #         update_success=False
        # if not update_success:
        #     flash("Error Updating stocks from external API", "danger")
        transactions=User.user_transactions
        users_list = User.query.order_by(User.total_asset_value).all()

        return render_template('/home.html', owned_stocks=owned_stocks, transactions=transactions, users_list=users_list)
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

@app.route('/users/edit', methods=["GET", "POST"])
def edit_user():
    """Show edit user form and validate and authenticate submission"""
    if g.user:
        form = UserEditForm(ojb=g.user)
        if form.validate_on_submit():
            if User.authenticate(g.user.username, form.password.data):
                g.user.username = form.username.data
                g.user.image_url = form.img_url.data
                
                db.session.commit()
                return redirect("/")
            else:
                flash("Wrong password, try again!", "danger")
                return redirect('/users/edit')
        else: 
            return render_template("/users/edit.html", form=form)
    else:
        flash("unauthorized access", "danger")

@app.route('/user/portfolio', methods=["GET", "POST"])
def show_portfolio():
    """
        Show current user's owned stocks, and value, valdiates submission 
        of buying and selling stocks
    """
    if g.user: 
        form = StockTransactionPorfolioForm()
        transaction_type = form.transaction_type.data
        amount = form.amount.data

        stocks = Owned_Stock.get_owned_stock_for_user(g.user.id)
        stock_ids = [stock.Owned_Stock.stock_id for stock in stocks]

        for stock_id in stock_ids:
            Stock.get_update(stock_id, True)
        
        if form.validate_on_submit():
            if len(form.data['stock_id']) > 10:
                raise Exception()               # WTForms does not validate HiddenField() field type
            stock_id = form.data['stock_id']

            try: 
                stock_id = int(stock_id)    #try coerce int
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
            return render_template("/users/portfolio.html",stocks=stocks, form=form)
    else:
        flash("Unauthorized Access", "danger")
        return redirect('/')


#********************************** STOCK ROUTES ****************************************
@app.route('/stocks', methods=['GET', 'POST'])
def show_stocks():
    """Shows search bar for searching stocks by name/symbol. Validates submission."""
    if g.user:
        form = StockSearchForm()

        if form.validate_on_submit():
            input_val = form.search._value()
            symbol = input_val[input_val.find("(")+1:input_val.find(")")]
            
            s = Stock.query.filter(Stock.stock_symbol == symbol).one()
            
            return redirect(f'/stocks/{s.id}')

        return render_template("/stocks/index.html", form=form)

    flash("Unauthorized Access", "danger")
    return redirect('/')
        
@app.route('/stocks/<int:stock_id>', methods=['GET', 'POST'])
def show_stock(stock_id):
    """Shows stock data of a particular stock. Also alows the user to buy/sell the stock"""
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
    """
        Returns JSON data of a particular stock. Used in javscript Axios 
        for retrieving complete stock data
    """
    if g.user:
        stock = Stock.query.get(stock_id)
        return jsonify(stock.data)
    else:
        return "unauthorized access", 401

@app.route('/api/stocks')
def get_stock_name_list():
    """
        Returns JSON data of a list of stock names and symbols.
        Used in the javascript Axios get request for autocompletion data.
    """
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

