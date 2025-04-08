from wtforms import Form
from flask_wtf import FlaskForm

from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, widgets
from wtforms import EmailField
from wtforms import validators
from wtforms.validators import DataRequired, Length, NumberRange

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange


class VentaForm(FlaskForm):
    galleta = StringField('Nombre de galleta', [
        validators.DataRequired(message='Es requerida la galleta')
    ])
    tipo_venta = StringField('Tipo de venta', [
        validators.DataRequired(message='Es requerido el tipo de venta')
    ])
    cantidad = IntegerField('Cantidad', [
        validators.DataRequired(message='Es requerida la cantidad'),
        validators.NumberRange(
            min=1, message='No puede haber cantidad negativas')
    ])


class PedidoForm(FlaskForm):
    cantidad = IntegerField('Cantidad', [
        validators.DataRequired(message='Es requerida la cantidad'),
        validators.NumberRange(
            min=1, message='No puede haber cantidad negativas')
    ])
