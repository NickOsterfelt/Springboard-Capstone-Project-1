from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from os import environ
import datetime

from flask import request
import requests

from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from forms import LoginSignupForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///stocks-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

CURR_USER_KEY = "curr_user"

app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

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
            flash(f"Hello, {user.username}, login successful!", "good")
            return redirect('/')

        flash("Invalid username/password combonation", "danger")
        return redirect('/login')

    return render_template('users/login.html', form = form)

@app.route('/stocks/<int:stock_id>')
def show_stock(stock_id):
    s = Stock.query.get(stock_id)
    if not Stock.get_update([s]):
        flash("rapidapi error updating stock data", "danger")
    return render_template('/stocks/details')

@app.route('/logout')
def logout():
    do_logout()
    return redirect('/')
    