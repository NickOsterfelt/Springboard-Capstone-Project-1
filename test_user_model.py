import os
from unittest import TestCase
from sqlalchemy import exc
from engine import seed_stock_symbol_and_names
from datetime import datetime

from models import db, User, Stock, Owned_Stock, Transaction

os.environ['DATABASE_URL'] = "postgresql:///stocks-app-test"

from app import app

db.create_all()

db.session.commit()

class UserModelTestCase(TestCase):
    """Tests user model"""

    def setUp(self):
        """Create test client, and sample user."""
        db.drop_all()
        db.create_all()

        u = User.signup("testing", "password")
        s = Stock(
            stock_symbol="TEST",
            name="TEST"
        )
        
        db.session.add(s)
        db.session.commit()
        
        self.u = User.query.get(u.id)

        self.s = Stock.query.get(s.id)
        self.uid = u.id

        self.client = app.test_client()
    
    def tearDown(self):
        """Revert db (called after each test)"""
        res = super().tearDown()
        db.session.rollback()
      
        return res

    def test_user_model(self):
        u = User(
            username="test1234",
            password="PASSWORD"
        )
        
        db.session.add(u)
        db.session.commit()
        
        self.assertEqual(u.total_asset_value, 0)
        self.assertEqual(len(u.user_transactions), 0)
        self.assertEqual(u.current_money, 10000)

    def test_user_transactions(self):
        """Tests that the user.user_transactions relationship is working"""
        self.assertEqual(len(self.u.user_transactions), 0)

        t = Transaction(
            user_id = self.u.id,
            stock_id = 1,
            stock_symbol="MMM",
            time = datetime.now(),
            quantity = 5,
            stock_value_at_time = 100.00,
            is_purchase = True
        )

        db.session.add(t)
        db.session.commit()

        u = User.query.get(self.u.id)
        
        self.assertEqual(len(u.user_transactions), 1)

    def test_valid_user_signup(self):
        """tests User.signup method with valid input"""
        u_test = User.signup("testtesttest", "testpassword")
        uid = 111
        u_test.id = uid
        db.session.commit()

        u_test = User.query.get(uid)

        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "testtesttest")
        self.assertNotEqual(u_test.password, "password")
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        """tests User.signup method with invalid username"""
        invalid = User.signup(None, "password")
        uid = 222
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        """tests User.signup method with invalid passwords"""
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "")
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", None)


    def test_valid_authentication(self):
        """Tests valaid authentication"""
        u = User.authenticate(self.u.username, "password")
        self.assertIsInstance(u, User)
        self.assertEqual(u.id, self.uid)
    
    def test_invalid_username(self):
        """Tests invalid username authentication"""
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        """Tests invalid password authentication"""
        self.assertFalse(User.authenticate(self.u.username, "badpassword"))

        
