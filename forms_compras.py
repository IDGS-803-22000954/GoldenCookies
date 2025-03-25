from wtforms import Form
from flask_wtf import FlaskForm
 
from wtforms import StringField,IntegerField,RadioField, SelectMultipleField, widgets
from wtforms import EmailField
from wtforms import validators
from wtforms.validators import DataRequired, Length, NumberRange
 
 
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange

class InsumoForm(FlaskForm):
    nombre = StringField('Nombre del Insumo', [
        validators.DataRequired(message='El nombre es requerido'),
        validators.Length(
            min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    unidad_medida = StringField('Unidad de Medida', [
        validators.DataRequired(message='La unidad de medida es requerida'),
        validators.Length(
            min=1, max=60, message='La unidad debe tener entre 1 y 60 caracteres')
    ])
    cantidad_insumo = StringField('Cantidad de insumo', [
        validators.DataRequired(message='La cantidad de insumo es requerida'),
        validators.Length(
            min=1, max=10, message='La unidad debe tener entre 1 y 10 caracteres')
    ])