from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, BooleanField, SubmitField
from wtforms import StringField, TextAreaField, RadioField, SubmitField, IntegerField, DateField, FloatField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed, FileRequired


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
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Login')

class RecipeForm(FlaskForm):
    recipename = StringField('Recipe Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration = IntegerField('Duration (in minutes)', validators=[DataRequired()])
    price = StringField('Price (in €)', validators=[DataRequired()])
    allergiesrec = StringField('Allergies Information', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients (JSON format)', validators=[DataRequired()])

    image = FileField('Recipe Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!'),
        Optional()  # De afbeelding is nu optioneel
    ])
    submit = SubmitField('Save Changes')

class ReviewForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    review_date = DateField('Review Date', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

class EditProfileForm(FlaskForm):
    email = StringField('E-mail', validators=[Email()], render_kw={'readonly': True})
    name = StringField('Full Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    street = StringField('Street', validators=[Optional(), Length(max=100)])
    housenr = IntegerField('House Number', validators=[Optional()])
    postalcode = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    country = StringField('Country', validators=[Optional(), Length(max=50)])
    telephonenr = StringField('Telephone', validators=[Optional(), Length(max=15)])
    is_chef = BooleanField('Are you a chef?')
    submit = SubmitField('Save Changes')
