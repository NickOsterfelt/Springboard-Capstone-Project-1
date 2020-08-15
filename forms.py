"""Forms for playlist app."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, BooleanField, IntegerField, RadioField, SelectField
from wtforms.validators import InputRequired, Email, Optional, Length

class LoginSignupForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(message="user-name is required"), Length(min=5, max=20, message="Length must be between 5 and 20 characters")])

    password = PasswordField('Password',validators=[Length(min=6, max=20, message="Password must be between 6-20 characters")])


