from wtforms import Form
from flask_wtf import FlaskForm
import re
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, widgets, BooleanField, SubmitField
from wtforms import EmailField
from wtforms import validators
from datetime import datetime
from wtforms import Form
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, NumberRange


class InsumoForm(FlaskForm):
    nombre = StringField('Nombre del Insumo', [
        validators.DataRequired(message='El nombre es requerido'),
        validators.Length(
            min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres'),
        validators.Regexp(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\.]+$',
                          message='El nombre solo puede contener letras, números, espacios y guiones')
    ])

    unidad_medida = SelectField('Unidad de Medida',
                                choices=[
                                    ('mililitros', 'Mililitros (ml)'),
                                    ('gramos', 'Gramos (g)'),
                                    ('unidades', 'Unidades (u)')
                                ],
                                validators=[
                                    DataRequired(
                                        message='La unidad de medida es requerida')
                                ]
                                )


class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre del Proveedor', [
        validators.DataRequired(
            message='El nombre del proveedor es requerido'),
        validators.Length(min=2, max=100),
        validators.Regexp(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.,\-]+$',
                          message='El nombre contiene caracteres no permitidos')
    ])

    contacto = StringField('Contacto del proveedor', [
        validators.DataRequired(message='El contacto es requerido'),
        validators.Length(min=1, max=100),
        validators.Regexp(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\@\.]+$',
                          message='El contacto contiene caracteres no permitidos')
    ])

    telefono = StringField('Teléfono de Proveedor', [
        validators.DataRequired(message='El teléfono es requerido'),
        validators.Length(min=8, max=20),
        validators.Regexp(r'^[\d\s\-\+\(\)]+$',
                          message='El teléfono solo puede contener dígitos, espacios y los caracteres +-()')
    ])


class CompraInsumoForm(FlaskForm):
    id_insumo = SelectField('Insumo', coerce=int, validators=[DataRequired()])
    id_proveedor = SelectField(
        'Proveedor', coerce=int, validators=[DataRequired()])

    presentacion = SelectField('Presentación', choices=[
        ('costal', 'Costal'),
        ('bolsa', 'Bolsa'),
        ('caja', 'Caja'),
        ('bulto', 'Bulto'),
        ('saco', 'Saco'),
        ('botella', 'Botella'),
        ('otro', 'Otro')
    ], validators=[DataRequired()])

    cantidad_presentaciones = FloatField('Cantidad de Presentaciones', validators=[
        DataRequired(),
        NumberRange(min=1, message='Debe ser al menos 1')
    ])

    peso_unitario = FloatField('Peso Unitario', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El peso debe ser mayor a cero')
    ])

    precio_total = FloatField('Costo Total', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El costo debe ser mayor a cero')
    ])

    unidad_medida = StringField(
        'Unidad de Medida', render_kw={'readonly': True})

    fecha_compra = DateField(
        'Fecha de Compra', default=datetime.today(), validators=[DataRequired()])
    fecha_caducidad = DateField(
        'Fecha de Caducidad', validators=[DataRequired()])
