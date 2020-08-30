import os
from unittest import TestCase
from sqlalchemy import exc
from engine import seed_stock_symbol_and_names
from datetime import datetime

from models import db, User, Stock, Owned_Stock, Transaction

os.environ['DATABASE_URL'] = "postgresql:///stocks-app-test"

from app import app

db.create_all()

class TransactionModelTestCase(TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

        u = User(
            username="testUser",
            password="testPassword"
        )
        s = Stock(
            stock_symbol="TEST",
            name="testStock",
            share_price = 1.01
        )
        db.session.add(u)
        db.session.add(s)
        db.session.commit()

        self.u = User.query.get(u.id)
        self.s = Stock.query.get(s.id)

        t = Transaction(
            stock_id = self.s.id,
            user_id = self.u.id,
            stock_symbol = s.stock_symbol,
            quantity = 10,
            time = datetime.now(),
            stock_value_at_time = 100.00,
            is_purchase = True
        )
        db.session.add(t)
        db.session.commit()
        self.t = t

    def tearDown(self):
        """Revert db (called after each test)"""
        res = super().tearDown()
        db.session.rollback()
      
        return res

    def test_transaction_model(self):
        """
            Tests that transactions are stored in the db and retrived by
            the ORM successfully.
        """
        t = Transaction.query.filter(Transaction.stock_id == self.s.id).one()
        self.assertIsNotNone(t)
        self.assertEqual(t.stock_id, self.s.id)
        self.assertEqual(t.user_id, self.u.id)
        self.assertEqual(self.t, t)

    def test_generate_transaction(self):
        """Tests Transaction.generate_transaction method"""
        Transaction.query.delete()
        db.session.commit()

        Transaction.generate_transaction(self.u, self.s, 10, True)
        db.session.commit()
        
        t = Transaction.query.filter(Transaction.user_id == self.u.id).one()

        self.assertEqual(t.user_id, self.u.id)
        self.assertEqual(t.stock_id, self.s.id)
        self.assertEqual(t.quantity, 10)
        self.assertEqual(t.is_purchase, True)

    def test_get_user_transaction(self):
        """
            Tests the Transaction.get_user_transactions method, which should
            get a list of transactions by the user specified by the passed in 
            user_id value.
        """
        user_transactions = Transaction.get_user_transactions(self.u.id)

        self.assertNotEqual(user_transactions, [])
        self.assertEqual(self.u.id, user_transactions[0].Transaction.user_id)
        self.assertEqual(self.s.id, user_transactions[0].Transaction.stock_id)
        self.assertEqual(self.s.name, user_transactions[0].name)

class OwnedStockModelTestCase(TestCase):
    
    def setUp(self):
        db.drop_all()
        db.create_all()

        u = User(
            username="testUser",
            password="testPassword"
        )
        
        s = Stock(
            stock_symbol="TEST",
            name="testStock",
            share_price = 1.01
        )

        db.session.add(u)
        db.session.add(s)
        db.session.commit()
        
        self.u = User.query.get(u.id)
        self.s = Stock.query.get(s.id)

        owned_stock = Owned_Stock()
        owned_stock.user_id = u.id
        owned_stock.stock_id = s.id
        owned_stock.quantity = 25
        owned_stock.value_when_purchased = s.share_price
        owned_stock.time = datetime.now()
        db.session.add(owned_stock)
        db.session.commit()

        # Owned_Stock.add_owned_stock_for_user(self.u, self.s, 25)
        db.session.commit()

    def tearDown(self):
        """Revert db (called after each test)"""
        res = super().tearDown()
        db.session.rollback()
      
        return res

    def test_owned_stock_model(self):
        """
            Tests that Owned_Stocks are stored in the db and retrived by
            the ORM successfully.
        """
        o = Owned_Stock.query.filter(Owned_Stock.user_id == self.u.id).one()
        self.assertIsNotNone(o)
        self.assertEqual(o.stock_id, self.s.id)
        self.assertEqual(o.user_id, self.u.id)
        

    def test_user_owns_stock(self):
        """
            The Owned_Stock.user_owns_stock method should return
            true or false whether the user owns a given stock or 
            not
        """
        s = Stock(
            name = "unownedStock",
            stock_symbol = "ABCDE"
        )
        u = User(
            username = "OwnsNothing",
            password = "test1234"
        )
        db.session.add(s)
        db.session.add(u)
        #user does own this stock
        self.assertTrue(Owned_Stock.user_owns_stock(self.u.id, self.s.id))
        #user does not own this stock
        self.assertFalse(Owned_Stock.user_owns_stock(self.u.id, s.id))
        self.assertFalse(Owned_Stock.user_owns_stock(u.id, self.s.id))


    def test_add_remove_owned_stock_for_user(self):
        """ 
            add_owned_stock_for_user should add a row to the owned_stocks table
            if the user does not already own it. If the user does own the stock,
            it should increment the amount owned and update the value purchased at.
            remove_owned_stock should do the opposite.
        """
        s1 = Stock(
            name = "stock1",
            stock_symbol="S1",
            share_price = 10.00
        )
        db.session.add(s1)
        db.session.commit()

        #test add stock that is not previously owned
        Owned_Stock.add_owned_stock_for_user(self.u, s1, 10)
        o = Owned_Stock.query.filter(Owned_Stock.stock_id == s1.id).one()
        self.assertEqual(o.user_id, self.u.id)
        self.assertEqual(o.quantity, 10)
        self.assertEqual(o.stock_id, s1.id)

        #test add stock that is already owned (should increment)
        Owned_Stock.add_owned_stock_for_user(self.u, s1, 10)
        o = Owned_Stock.query.filter(Owned_Stock.stock_id == s1.id).all()
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0].quantity, 20)
        self.assertEqual(o[0].user_id, self.u.id)
        self.assertEqual(o[0].stock_id, s1.id)

        #test remove stock that is owned
        Owned_Stock.remove_owned_stock_for_user(self.u, s1, 1)
        o = Owned_Stock.query.filter(Owned_Stock.stock_id == s1.id).all()
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0].quantity, 19)
        self.assertEqual(o[0].user_id, self.u.id)
        self.assertEqual(o[0].stock_id, s1.id)

        #test remove more than stock that is owned
        Owned_Stock.remove_owned_stock_for_user(self.u, s1, 25)
        o = Owned_Stock.query.filter(Owned_Stock.stock_id == s1.id).all()
        self.assertEqual(len(o), 0)
        
    


        