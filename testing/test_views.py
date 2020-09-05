# run these tests like:
#
#    FLASK_ENV=production python -m unittest testing/test_views.py


import os
from unittest import TestCase
from datetime import datetime
from bs4 import BeautifulSoup

from forms import StockTransactionForm
from models import db, User, Stock, Owned_Stock, Transaction, App_Config
from engine.engine import *

os.environ['DATABASE_URL'] = "postgresql:///stocks-app-test"

from app import app, CURR_USER_KEY

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

#disables getting updates from external apis
def setup_test_app_config():
    a = App_Config(name="GET_LARGE_UPDATES", toggle=False)  
    b = App_Config(name="GET_SMALL_UPDATES", toggle=False) 
    db.session.add_all([a,b])
    db.session.commit()

class TestUserViews(TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

        setup_test_app_config()
        self.client = app.test_client()

        self.testuser = User.signup("testuser", "testuser")
        
        self.testuser_id=1234
        self.testuser.id=self.testuser_id

        self.u1 = User.signup("testuser1", "testuser1")
        self.u1_id = 111
        self.u1.id = self.u1_id
        self.u2 = User.signup("testuser2", "testuser2")
        self.u2_id = 222
        self.u2.id = self.u2_id
        self.u3 = User.signup("testuser3", "testuser3")
        self.u4 = User.signup("testuser4", "testuser4")

        s1 = Stock(stock_symbol="TEST1", name="testStock1", share_price = 10)
        s2 = Stock(stock_symbol="TEST2", name="testStock2", share_price = 20)
        s3 = Stock(stock_symbol="TEST3", name="testStock3", share_price = 30)

        db.session.add_all([s1,s2,s3])
        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp
    
    def test_user_homepage(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get("/", follow_redirects=True)

            self.assertIn("testuser", str(resp.data))
            self.assertIn("testuser1", str(resp.data))
            self.assertIn("testuser2", str(resp.data))
            self.assertIn("testuser3", str(resp.data))
            self.assertIn("testuser4", str(resp.data))

    def test_user_edit_view(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get("/users/edit")

            self.assertIn("testuser", str(resp.data))
            self.assertIn("To confirm changes, enter your password", str(resp.data))
    
    def setup_owned_stocks(self):
        o1 = Owned_Stock(user_id=self.testuser_id, stock_id=1, quantity=10, value_when_purchased=10)
        o2 = Owned_Stock(user_id=self.testuser_id, stock_id=2, quantity=10, value_when_purchased=20)
        
        db.session.add_all([o1,o2])
        db.session.commit()

    def test_user_home_with_stocks(self):
        self.setup_owned_stocks()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get("/", follow_redirects=True)

            self.assertIn("TEST1", str(resp.data))
            self.assertIn("testStock1", str(resp.data))
            self.assertIn("100", str(resp.data))
            self.assertIn("TEST2", str(resp.data))
            self.assertIn("testStock2", str(resp.data))
            self.assertIn("200", str(resp.data))
            
            self.assertNotIn("TEST3", str(resp.data))
            self.assertNotIn("testStock3", str(resp.data))

    def setup_transactions(self):
        t1 = Transaction(user_id=self.testuser_id, stock_id = 1, quantity = 10, stock_symbol="TEST1", time=datetime.now(), stock_value_at_time=10, is_purchase=True)
        t2 = Transaction(user_id=self.testuser_id, stock_id = 2, quantity = 20, stock_symbol="TEST2", time=datetime.now(), stock_value_at_time=20, is_purchase=True)
        t3 = Transaction(user_id=self.testuser_id, stock_id = 1, quantity = 10, stock_symbol="TEST1", time=datetime.now(), stock_value_at_time=30, is_purchase=False)
        
        db.session.add_all([t1,t2,t3])
        db.session.commit()

    def test_user_home_with_transactions(self):
        self.setup_transactions()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
                
            resp = c.get("/", follow_redirects=True)

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            transaction_list = soup.find_all(class_="transaction-list")
            tds = transaction_list[0].find_all("td")
            self.assertEqual(len(tds), 15)

            t1s = transaction_list[0].find_all("td",text="TEST1")
            self.assertEqual(len(t1s), 2)

            t2s = transaction_list[0].find_all("td",text="TEST2")
            self.assertEqual(len(t2s), 1)

class TestStockViews(TestCase):
    #Currently Fails due to csrf_token field in jinja template. 
    def setUp(self):
        db.drop_all()
        db.create_all()

        Stock.query.delete()
        setup_test_app_config()

        self.client = app.test_client()

        self.testuser = User.signup("testuser", "testuser")
        
        self.testuser_id=1234
        self.testuser.id=self.testuser_id

        s1 = Stock(stock_symbol="TEST1", name="testStock1", share_price = 10)
        s2 = Stock(stock_symbol="TEST2", name="testStock2", share_price = 20)
        s3 = Stock(stock_symbol="TEST3", name="testStock3", share_price = 30)
        db.session.add_all([s1,s2,s3])
        db.session.commit()
        
        self.stock_id=s1.id

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

   
    def test_stock_view(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
        
            resp = c.get(f"/stocks/{self.stock_id}", follow_redirects=True)
        
            self.assertIn("testStock1", str(resp.data))
            self.assertIn("Share Price", str(resp.data))     
            self.assertIn("$10", str(resp.data))    
            self.assertIn("Buy/Sell", str(resp.data))
            self.assertIn("# of shares", str(resp.data))
            self.assertIn("Current Amount Owned: 0", str(resp.data))

    def test_stock_buy(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
        
            form_data = dict(amount=10, transaction_type="buy", stock_id=1)
            resp = c.post("/stocks/1", data = form_data, follow_redirects=True)

            self.assrtIn("Transaction Successful!", str(resp.data))
            self.assrtIn("Current Amount Owned: 10", str(resp.data))
