import re
from wtforms import EmailField, Form, PasswordField, SelectField, SubmitField, TelField, ValidationError
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, widgets
from wtforms import validators


def validar_contrasenia(form, field):
    contrasenia = field.data

    # Verifica si hay más de 3 caracteres iguales seguidos
    if re.search(r'(.)\1{2,}', contrasenia):  
        raise ValidationError("La contraseña no puede contener más de 3 caracteres iguales seguidos.")

    # Verifica si contiene al menos una letra mayúscula
    if not re.search(r'[A-Z]', contrasenia):  
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")

    # Verifica si contiene al menos un número
    if not re.search(r'\d', contrasenia):  
        raise ValidationError("La contraseña debe contener al menos un número.")

    # Verifica si contiene al menos un carácter especial
    if not re.search(r'[!@#$%^&*]', contrasenia):  
        raise ValidationError("La contraseña debe contener al menos un carácter especial (!@#$%^&*).")



class loginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired(message="El nombre de usuario es requerido")])
    password = PasswordField('Password', [validators.DataRequired(message="El pasword es requerido")])
    submit = SubmitField('login')


class RegistroForm(FlaskForm):
    nombre = StringField('Nombre', [validators.DataRequired(message="El nombre es requerido"), 
                                    validators.Length(max=100)])
    nombre_usuario = StringField('Nombre de Usuario', [validators.DataRequired(message="El nombre de usuario es requerido"), 
                                                    validators.Length(max=50)])
    telefono = TelField('Teléfono', [validators.DataRequired(message="El telefono es requerido"), 
                                    validators.Length(max=15)])
    email = EmailField('Email', [validators.DataRequired(message="El email es requerido"), 
                                validators.Length(max=50)])
    contrasenia = PasswordField('Contraseña', [validators.DataRequired(message="La contraseña es requerida"), 
                                            validators.Length(min=6, max=255), 
                                            validar_contrasenia])
    confirmar_contrasenia = PasswordField('Confirmar Contraseña', [validators.DataRequired(message="El campo es requerido"), 
                                                                validators.EqualTo('contrasenia', message='Las contraseñas deben coincidir.')
    ])
    submit = SubmitField('Registrar')

class logoutForm(FlaskForm):
    submit = SubmitField('logout')

class EditarPerfilForm(FlaskForm):
    nombre = StringField('Nombre', [validators.DataRequired(), validators.Length(min=2, max=100)])
    nombre_usuario = StringField('Nombre de Usuario', [validators.DataRequired(), validators.Length(min=4, max=50)])
    telefono = StringField('Teléfono', [validators.DataRequired(), validators.Length(min=8, max=15)])
    email = StringField('Correo Electrónico', [validators.DataRequired(), validators.Email()])
    contrasenia = PasswordField('Nueva Contraseña (opcional)', [validators.Optional(), validators.Length(min=6)])
    submit = SubmitField('Guardar cambios')


class RegistroForm_adm(FlaskForm):
    nombre = StringField('Nombre', [validators.DataRequired(message="El nombre es requerido"), 
                                    validators.Length(max=100)])
    nombre_usuario = StringField('Nombre de Usuario', [validators.DataRequired(message="El nombre de usuario es requerido"), 
                                                    validators.Length(max=50)])
    telefono = TelField('Teléfono', [validators.DataRequired(message="El telefono es requerido"), 
                                    validators.Length(max=15)])
    email = EmailField('Email', [validators.DataRequired(message="El email es requerido"), 
                                validators.Length(max=50)])
    contrasenia = PasswordField('Contraseña', [validators.DataRequired(message="La contraseña es requerida"), 
                                            validators.Length(min=8, max=255), 
                                            validar_contrasenia])
    confirmar_contrasenia = PasswordField('Confirmar Contraseña', [validators.DataRequired(message="El campo es requerido"), 
                                                                validators.EqualTo('contrasenia', message='Las contraseñas deben coincidir.')
    ])
    
    rol = SelectField('Rol', choices=[
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
        ('ventas', 'Vendedor'),
        ('produccion', 'Produccion')
    ], validators=[validators.DataRequired(message="El rol es requerido")])

    submit = SubmitField('Registrar')
