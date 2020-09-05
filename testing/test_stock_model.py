import os
from unittest import TestCase
from sqlalchemy import exc
from engine.engine import seed_stock_symbol_and_names, setup_app_config
from datetime import datetime

from models import db, User, Stock, Owned_Stock, Transaction

os.environ['DATABASE_URL'] = "postgresql:///stocks-app-test"

from app import app

db.create_all()

setup_app_config()

class StockModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        db.drop_all()
        db.create_all()
        seed_stock_symbol_and_names()   

    @classmethod
    def tearDownClass(cls):
        Stock.query.delete()
        db.session.rollback()

    def setUp(self):
        
        s = Stock.query.get(1)
        self.stock = s

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_stock_model(self):
        """test that stocks are being stored in the database and retrived by the ORM correctly"""
        self.assertEqual(self.stock.name, "3M Company")
        self.assertEqual(self.stock.stock_symbol, "MMM")

    def test_stock_get_update(self):
        """
            Tests Stock.get_update method which should use the external api
            to get updated stock data. This is tested by comparing results
            before and after the get_upate is called.
        """
        before = Stock(
            name = self.stock.name,
            stock_symbol=self.stock.stock_symbol,
            data = self.stock.data,
            share_price=self.stock.share_price,
            last_updated=self.stock.last_updated
        )

        if Stock.get_update(self.stock.id):
            after = Stock.query.get(self.stock.id)
            self.assertEqual(before.name, after.name)
            self.assertEqual(before.stock_symbol, after.stock_symbol)
            self.assertNotEqual(before.data, after.data)
            self.assertNotEqual(before.share_price, after.share_price)
            self.assertNotEqual(before.last_updated, after.last_updated)
        else:
            self.fail("Problem retrieving data from external API")

        

        


