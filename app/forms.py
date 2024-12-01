from flask_wtf import FlaskForm
<<<<<<< HEAD
from wtforms import StringField, DateField, IntegerField, BooleanField, SubmitField
=======
from wtforms import StringField, TextAreaField, FloatField, SubmitField, IntegerField, DateField
>>>>>>> 2e6c500332b7fdb9e297f2c957490655f84c081f
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    date_of_birth = DateField('Geboortedatum', validators=[DataRequired()])
    street = StringField('Street', validators=[DataRequired()])
    housenr = IntegerField('Housnumber', validators=[DataRequired()])
    postalcode = IntegerField('Postalcode', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    telephonenr = StringField('Telephone', validators=[DataRequired(), Length(max=15)])
    
    # Toevoeging van het is_chef veld als een BooleanField
    is_chef = BooleanField('Are you a chef?', validators=[DataRequired()])

    submit = SubmitField('Save')



class LoginForm(FlaskForm):
    email = StringField('Emai', validators=[DataRequired()])
    submit = SubmitField('Login')

class RecipeForm(FlaskForm):
    recipename = StringField('Recipe Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration = IntegerField('Duration (in minutes)', validators=[DataRequired()])
    price = StringField('Price (in €)', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    allergiesrec = StringField('Allergies Information', validators=[DataRequired()])
    image = StringField('Image URL', validators=[DataRequired()])
    submit = SubmitField('Add Recipe')