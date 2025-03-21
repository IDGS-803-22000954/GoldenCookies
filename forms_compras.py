from wtforms import Form
from flask_wtf import FlaskForm
 
from wtforms import StringField,IntegerField,RadioField, SelectMultipleField, widgets
from wtforms import EmailField
from wtforms import validators
from wtforms.validators import DataRequired, Length, NumberRange
 
 

 
 
class ComprasForm(Form):
    id=IntegerField('id',
    [validators.number_range(min=1, max=20,message='valor no valido')])
    nombre=StringField('nombre',[
        validators.DataRequired(message='El nombre es requerido'),
    ])
   
    direccion=StringField('direccion',[
        validators.DataRequired(message='La dirección es requerido')
    ])
   
    telefono=StringField('telefono',[
        validators.DataRequired(message='El telefono es requerido')
    ])
    tamanio = RadioField('Tamaño', choices=[('pequeño', 'Pequeño'), ('mediano', 'Mediano'), ('grande', 'Grande')], 
                         validators=[DataRequired(message='Selecciona un tamaño')])
    
    ingredientes = SelectMultipleField('Ingredientes', choices=[
        ('queso', 'Queso Extra'),
        ('peperoni', 'Peperoni'),
        ('champiñones', 'Champiñones')
    ], validators=[DataRequired(message='Selecciona al menos un ingrediente')])
    
    numerop=IntegerField('numerop',[
        validators.DataRequired(message='El número de pizzas es requerido')
    ])


class UserForm(FlaskForm):
    id=IntegerField('id',
    [validators.number_range(min=1, max=20,message='valor no valido')])
    nombre = StringField('Nombre', [
        validators.DataRequired(message='El nombre es requerido'),
        validators.length(
            min=4, max=25, message='El nombre debe tener entre 4 y 25 caracteres')
    ])
    direccion = StringField('Dirección', [
        validators.DataRequired(message='La dirección es requerida'),
        validators.length(
            min=4, max=100, message='La dirección debe tener entre 4 y 100 caracteres')
    ])
    telefono = StringField('Teléfono', [
        validators.DataRequired(message='El teléfono es requerido'),
        validators.length(
            min=7, max=12, message='El teléfono debe tener entre 7 y 12 caracteres')
    ])


class FormPizza(FlaskForm):
    tamanio = RadioField(
        'Tamaño',
        choices=[('pequena', 'Pequeña ($40)'),
                 ('mediana', 'Mediana ($80)'),
                 ('grande', 'Grande ($120)')],
        default='mediana',
        validators=[validators.DataRequired(message='El tamaño es requerido')])

    ingredientes = SelectMultipleField('Ingredientes ($10 cada uno)',choices=[
            ('jamon', 'Jamón'),
            ('pina', 'Piña'),
            ('champinones', 'Champiñones')
        ],
        default=['jamon'],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )

    numerop = IntegerField('Número de pizzas', [
        validators.DataRequired(message='Número de pizzas es requerido'),
        validators.NumberRange(
            min=1, max=100, message='El número de pizzas debe ser mayor que 1')
    ], default=1)