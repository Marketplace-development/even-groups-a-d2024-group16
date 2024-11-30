from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    date_of_birth = DateField('Geboortedatum', validators=[DataRequired()])
    street = StringField('Street', validators=[DataRequired()])
    housenr = IntegerField('Housnumber', validators=[DataRequired()])
    postalcode = IntegerField('postalcode', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    telephonenr = StringField('Telephone', validators=[DataRequired(), Length(max=15)])
    submit = SubmitField('Save')

class LoginForm(FlaskForm):
    email = StringField('Emai', validators=[DataRequired()])
    submit = SubmitField('Login')