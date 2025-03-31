from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user
import requests
from models import usuario  # Asegúrate de que el modelo esté bien definido en models.py
from werkzeug.security import check_password_hash, generate_password_hash
from utils import generar_codigo_2fa  # Importa funciones auxiliares
from models import db 
from forms import loginForm, RegistroForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        # Validar reCAPTCHA
        recaptcha_response = request.form['g-recaptcha-response']
        secret_key = '6LcQ1QQrAAAAAJyd5S8evLqIYJOeqIiuacXJ9b_M'
        payload = {
            'response': recaptcha_response,
            'secret': secret_key
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()

        if not result.get('success'):
            flash('Por favor completa el reCAPTCHA.', 'danger')
            return redirect(url_for('login'))
        
        nombre_usuario = form.username.data
        contrasenia = form.password.data

        user = usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if not user:
            flash('El usuario no existe. Regístrate primero.', 'warning')
            return redirect(url_for('login'))

        if user.bloqueado:
            flash('Tu cuenta está bloqueada. Contacta al soporte.', 'danger')
            return redirect(url_for('login'))

        if not check_password_hash(user.contrasenia, contrasenia):
            user.intentos_fallidos += 1
            if user.intentos_fallidos >= 5:
                user.bloqueado = True
                flash('Cuenta bloqueada por intentos fallidos.', 'danger')
            db.session.commit()
            return redirect(url_for('login'))

        # Restablecer intentos fallidos
        user.intentos_fallidos = 0
        db.session.commit()

        generar_codigo_2fa(user)

        session['id_usuario'] = user.id_usuario
        return redirect(url_for('auth.verificar_codigo_2fa'))

    return render_template('auth/login.html', form=form)


@auth.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()

    if form.validate_on_submit():
        # Validar reCAPTCHA
        recaptcha_response = request.form['g-recaptcha-response']
        secret_key = '6LcQ1QQrAAAAAJyd5S8evLqIYJOeqIiuacXJ9b_M'
        payload = {
            'response': recaptcha_response,
            'secret': secret_key
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()

        if not result.get('success'):
            flash('Por favor completa el reCAPTCHA.', 'danger')
            return redirect(url_for('auth.registro'))
        
        # Hashear la contraseña antes de almacenarla
        hashed_password = generate_password_hash(form.contrasenia.data)

        user = usuario(
            nombre=form.nombre.data,
            nombre_usuario=form.nombre_usuario.data,
            telefono=form.telefono.data,
            email=form.email.data,
            contrasenia=hashed_password  # Guardar la contraseña encriptada
        )
        
        db.session.add(user)
        db.session.commit()

        # Autenticar al usuario recién registrado
        login_user(user)

        flash('Usuario registrado y autenticado con éxito!', 'success')
        return redirect(url_for('cliente'))  # Redirigir al menú

    return render_template('auth/registro.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()  # Cierra la sesión
    flash("Has cerrado sesión exitosamente", "success")  # Mensaje opcional
    return redirect(url_for('auth.login'))

@auth.route('/verificar_2fa', methods=['GET', 'POST'])
def verificar_codigo_2fa():
    user = usuario.query.get(session.get('id_usuario'))
    if not user:
        flash('Usuario no encontrado. Inicia sesión de nuevo.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo_2fa')
        
        # Verificar si el código ingresado coincide con el código en la sesión
        if codigo_ingresado == session.get('codigo_2fa'):
            login_user(user)
            user.codigo_2fa = ''
            db.session.commit()
            
            if user.rol.lower() == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.rol.lower() == 'produccion':
                return redirect(url_for('produccion_dashboard'))
            elif user.rol.lower() == 'ventas':
                return redirect(url_for('ventas_dashboard'))
            elif user.rol.lower() == 'cliente':
                return redirect(url_for('cliente'))
            else:
                flash('Rol no reconocido.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Código incorrecto. Inténtalo de nuevo.', 'danger')
    
    return render_template('auth/verificar_2fa.html')


@auth.route('/reenviar_codigo', methods=['GET', 'POST'])
def reenviar_codigo():
    """Endpoint para reenviar el código 2FA."""
    user_id = session.get('id_usuario')
    user = usuario.query.get(user_id)

    if user:
        generar_codigo_2fa(user)  # Regenerar el código y enviarlo de nuevo
        return redirect(url_for('auth.verificar_codigo_2fa'))  # Redirigir a la página de verificación
    else:
        flash('Usuario no encontrado. Inicia sesión nuevamente.', 'danger')
        return redirect(url_for('auth.login'))

@auth.route('/perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'id_usuario' not in session:
        flash("Debes iniciar sesión para acceder a tu perfil.", "warning")
        return redirect(url_for('auth.login'))

    user = usuario.query.get(session['id_usuario'])

    if request.method == 'POST':
        user.nombre = request.form['nombre']
        user.nombre_usuario = request.form['nombre_usuario']
        user.telefono = request.form['telefono']
        user.email = request.form['email']

        nueva_contrasenia = request.form['contrasenia']
        if nueva_contrasenia:
            user.contrasenia = generate_password_hash(nueva_contrasenia)

        db.session.commit()
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for('auth.editar_perfil'))

    return render_template('perfil.html', usuario=user)