from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from os import environ
import datetime
import json

from flask import request
import requests

from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from forms import LoginSignupForm
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

#********************************** STOCK ROUTES ****************************************
@app.route('/stocks')
def show_stocks():
    if g.user:
        return render_template("/stocks/index.html")

    return redirect('/')
        
@app.route('/stocks/<int:stock_id>')
def show_stock(stock_id):
    if g.user:
        stock = Stock.query.get(stock_id)
        #data = Stock.get_update(stock_id, True)    #WARNING CALLS EXTERNAL API, ENABLE LATER when done testing
        data = {}
        with open('sample.json') as json_file:         #loads sample data
            data = json.load(json_file)
        if not data:                                   
            flash("Error getting update from external API", "danger")
            return redirect("/")

        return render_template('/stocks/details.html', stock=stock, data=data)

    return redirect('/')



# *********************************** API ************************************************
@app.route('/api/<int:stock_id>')
def get_stock_data(stock_id):
    if g.user:
        stock = Stock.query.get(stock_id)
        return jsonify(stock.data)
    else:
        return "unauthorized access", 401


    