from models import User, Stock, connect_db, Transaction, Owned_Stock, db
from app import app
from datetime import datetime

import csv

db.drop_all()
db.create_all()

User.query.delete()
Stock.query.delete()
Owned_Stock.query.delete()
Transaction.query.delete()


#stocks
#seed stocks with symbols and names
with open('stock_seed_data.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        s = Stock()
        s.stock_symbol = row[0]
        s.name = row[1]
        s.last_updated = datetime.now()
        db.session.add(s)
db.session.commit()
s = Stock.query.get(1)

#users
u = User.signup("test1", "123456")

u1 = User.signup("test2", "123456")


db.session.commit()

#owned stocks
o = Owned_Stock()
o.stock_id = s.id
o.user_id = u.id
o.time = datetime.now()
o.quantity = 10
o.value_when_purchased = 100.00
db.session.add(o)
db.session.commit()

#transactions
t = Transaction()
t.user_id = u.id
t.stock_id = s.id
t.is_purchase = True
t.stock_symbol = "AMAT"
t.stock_value_at_time = 100.00
t.quantity = 10
t.time = datetime.now()

db.session.add(t)
db.session.commit()








