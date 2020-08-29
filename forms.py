"""Forms for Stock app."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, BooleanField, IntegerField, RadioField, SelectField, HiddenField
from wtforms.validators import InputRequired, Email, Optional, Length, NumberRange


class LoginSignupForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(message="user-name is required"), Length(min=5, max=20, message="Length must be between 5 and 20 characters")])
    password = PasswordField('Password',validators=[Length(min=6, max=20, message="Password must be between 6-20 characters")])

class UserEditForm(LoginSignupForm):
    img_url = StringField("Profile Picture Url", validators=[Length(min=0, max=5000, message="image link too long!")])

class StockTransactionForm(FlaskForm):
    amount = IntegerField("# of shares", validators=[InputRequired(message="Enter an amount"), NumberRange(min=1)])
    transaction_type = RadioField(choices=[("buy", "Buy" ), ("sell", "Sell")], default="buy")
    stock_id = HiddenField()

class StockSearchForm(FlaskForm):
    search = StringField("Search", validators=[InputRequired(message="input required"), Length(max=50)])


