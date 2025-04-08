from wtforms import Form
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, RadioField, SelectMultipleField, widgets, SelectField, FileField, HiddenField
from flask_wtf.file import FileAllowed
from wtforms import EmailField
from wtforms import validators
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from models import Galleta, Receta, RecetaInsumo
from flask import current_app
from flask import session
from flask import g
from models import db


class RecetaForm(FlaskForm):
    nombre = StringField('Nombre de la Receta', [
        validators.DataRequired(message='El nombre es requerido'),
        validators.Length(
            min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])

    cantidad_produccion = IntegerField('Cantidad Producida', [
        validators.DataRequired(message='La cantidad es requerida'),
        validators.NumberRange(
            min=0, max=200, message='La cantidad debe ser mayor a 0')
    ])

    detalles = StringField('Detalles de la receta', [
        validators.DataRequired(message='Los detalles son requeridos'),
        validators.Length(
            min=1, max=3000, message='La unidad debe tener entre 1 y 3000 caracteres')
    ])

    descripcion = StringField('Descripción de la galleta', [
        validators.DataRequired(message='Los detalles son requeridos'),
        validators.Length(
            min=1, max=250, message='La descripción debe tener entre 1 y 250 caracteres')
    ])

    id_galleta = HiddenField()
    id_receta = SelectField('Seleccionar Galleta', coerce=int, choices=[
    ], validators=[DataRequired()])

    peso_unidad = FloatField('Peso unidad', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El peso debe ser mayor a cero')
    ])

    imagen_galleta = FileField('Imagen', validators=[
                               FileAllowed(['jpg', 'jpeg', 'png'], 'Solo imágenes')])

    def cargar_opciones(self):
        from models import Galleta
        self.id_receta.choices = [(g.id_galleta, g.nombre)
                                  for g in Galleta.query.all()]


class RecetaInsumoForm(FlaskForm):
    nombre_insumo = StringField('Ingredientes', [
        validators.DataRequired(message='Los ingredientes son requeridos'),
        validators.Length(
            min=2, max=100, message='Los ingredientes deben tener entre 2 y 100 caracteres')
    ])

    cantidad_insumo = StringField('Cantidad Insumo', validators=[
        DataRequired(),
        Length(min=1, max=10)
    ])


def validate_cantidad_insumo(self, field):
    try:
        float(field.data.replace(',', '.'))
    except ValueError:
        raise validators.ValidationError('Debe ingresar un número válido.')
