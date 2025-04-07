
from wtforms import Form, FloatField, StringField, validators, HiddenField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
import re


class GalletaForm(FlaskForm):
    id_galleta = HiddenField()
    nombre = StringField('Nombre de la Galleta', [
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])

    precio_sugerido = FloatField('Precio sugerido', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El precio debe ser mayor a cero')
    ])

    peso_unidad = FloatField('Peso unidad', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El peso debe ser mayor a cero')
    ])

    descripcion = StringField('Descripción de la galleta', [
        DataRequired(message='Los detalles son requeridos'),
        Length(min=1, max=250,
               message='La descripción debe tener entre 1 y 250 caracteres')
    ])
