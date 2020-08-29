from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
from models import db, connect_db, User, Stock, Owned_Stock, Transaction
from constants import * 
from exceptions import * 

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        g.user = None
        del session[CURR_USER_KEY]
    else:
        raise Exception()
    
def authenticate_user_edit(form):
    """Verifies user password when submitting user edit form"""
    if User.authenticate(g.user.username, form.password.data):
            db.session.add(g.user)
            db.session.commit()
            return True

    return False

def validate_stock_transaction_form(form):
    """
        Validates that a StockTransactionForm has valid inputs. stock_id, a Hidden field, is manually
        verified where WTForms does not support validation. 
    """
    try:
        form.data['stock_id']
    except KeyError:
        raise InvalidFormInput("stock_id", "missing", "form is missing stock_id hidden field")

    if len(form.data['stock_id']) > 10:
        raise InvalidFormInput("stock_id", form.data["stock_id"], "stock_id length is too long to be valid")   

    stock_id = form.data['stock_id']

    try: 
        stock_id = int(stock_id)    #try coerce int
    except ValueError:
        raise InvalidFormInput("stock_id", stock_id, "stock_id must be an integer")

def do_transaction(form):
    """
        Does a stock transaction using the User.buy_stock() and User.sell_stock() methods, based on the input form data.
        The form must be a validated StockTransactionForm type.
    """
    stock_id = form.data['stock_id']
    amount = form.data['amount']
    transaction_type = form.data["transaction_type"]

    if transaction_type == "buy":
        if g.user.buy_stock(amount, stock_id):
            return True
        else:
            return False
    if transaction_type == "sell":
        if g.user.sell_stock(amount, stock_id):
            return True
        else:
            return False

def update_user_stocks(owned_stocks):
    """
        Takes a list of OwnedStocks as owned_stocks, and updates them using the external API.
        This can be time consuming given that the external api takes around 1 second per stock
        when getting updates.
    """
    
    update_success = True

    for stock in owned_stocks:          #TODO: AJAX requests. It is too slow on its own
        if not Stock.get_update(stock.Owned_Stock.stock_id):
            update_success=False
    if not update_success:
        return False
    return True