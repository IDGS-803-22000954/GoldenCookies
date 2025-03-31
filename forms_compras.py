from wtforms import Form
from flask_wtf import FlaskForm
import re
from wtforms import StringField,IntegerField,RadioField, SelectMultipleField, widgets,BooleanField, SubmitField
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
        validators.Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres'),
        validators.Regexp(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\.]+$', 
                         message='El nombre solo puede contener letras, números, espacios y guiones')
    ])
    
    unidad_medida = StringField('Unidad de Medida', [
        validators.DataRequired(message='La unidad de medida es requerida'),
        validators.Length(min=1, max=60),
        validators.Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                         message='La unidad de medida solo puede contener letras y espacios')
    ])
    
    cantidad_insumo = StringField('Cantidad de insumo', [
        validators.DataRequired(message='La cantidad de insumo es requerida'),
        validators.Length(min=1, max=10),
        validators.Regexp(r'^\d+(\.\d{1,2})?$',
                         message='La cantidad debe ser un número con hasta 2 decimales y mayor o igual a 0')
    ])

    

class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre del Proveedor', [
        validators.DataRequired(message='El nombre del proveedor es requerido'),
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
    id_proveedor = SelectField('Proveedor', coerce=int, validators=[DataRequired()])
    cantidad = FloatField('Cantidad', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='La cantidad debe ser mayor a cero')
    ])
    costo_unitario = FloatField('Costo Unitario', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='El costo debe ser mayor a cero')
    ])
    presentacion = StringField('Presentación', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    fecha_compra = DateField('Fecha de Compra', default=datetime.today(), validators=[DataRequired()])
    fecha_caducidad = DateField('Fecha de Caducidad', validators=[DataRequired()])