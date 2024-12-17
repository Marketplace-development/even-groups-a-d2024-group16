from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, BooleanField, SubmitField, SelectMultipleField, widgets
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
    
    # Radioknoppen om aan te geven of de gebruiker een chef is
    is_chef = RadioField(
        'Are you a chef?', 
        choices=[('true', 'Yes'), ('false', 'No')], 
        validators=[DataRequired()]
    )
    
    # Dynamische keuzes voor voorkeuren
    allergies = SelectMultipleField(
        'Allergies',
        choices=[],  # Wordt dynamisch ingesteld in de route
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
        coerce=str
    )
    favorite_ingredients = StringField('Favorite Ingredients')  # Dit wordt nu een enkel invoerveld
    favorite_origins = SelectMultipleField(
        'Favorite Origins',
        choices=[],  # Wordt dynamisch ingesteld in de route
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
        coerce=str
    )
    
    submit = SubmitField('Register')




class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Login')


class RecipeForm(FlaskForm):
    recipename = StringField('Recipe Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration = IntegerField('Duration (in minutes)', validators=[DataRequired()])
    price = StringField('Price (in €)', validators=[DataRequired()])
    allergiesrec = SelectMultipleField(
        'Allergies',
        choices=[],  # Wordt later in de route ingesteld
        coerce=str
    )
    # Nieuwe velden voor origin, category en preparation
    origin = StringField('Origin', validators=[Optional()])  # Optioneel
    category = StringField('Category', validators=[Optional()])  # Optioneel
    preparation = TextAreaField('Preparation Instructions', validators=[Optional()])  # Optioneel

    # Afbeelding van het recept, optioneel veld
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
    
    # Dynamische voorkeuren
    allergies = SelectMultipleField(
        'Allergies',
        choices=[],  # Wordt ingesteld in de route
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
        coerce=str
    )
    favorite_ingredients = StringField(
        'Favorite Ingredients',
        default=''  # Zorgt ervoor dat het veld nooit None is
)
    favorite_origins = SelectMultipleField(
        'Favorite Origins',
        choices=[],  # Wordt ingesteld in de route
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
        coerce=str
    )

    # Alleen zichtbaar voor admins of specifieke rollen
    is_chef = BooleanField('Are you a chef?')
    submit = SubmitField('Save Changes')


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    is_public = BooleanField('Make this comment public')  # Checkbox for public visibility
    submit = SubmitField('Send Message')
