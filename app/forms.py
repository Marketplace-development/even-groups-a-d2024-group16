from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, BooleanField, SubmitField
from wtforms import StringField, TextAreaField, RadioField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    street = StringField('Street', validators=[DataRequired()])
    housenr = IntegerField('Housenumber', validators=[DataRequired()])
    postalcode = IntegerField('Postalcode', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    telephonenr = StringField('Telephone', validators=[DataRequired(), Length(max=15)])
    
    # Verander BooleanField naar RadioField voor radioknoppen "Yes" en "No"
    is_chef = RadioField('Are you a chef?', choices=[('true', 'Yes'), ('false', 'No')], validators=[DataRequired()])

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