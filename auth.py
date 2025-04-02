from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
import requests
from models import usuario
from werkzeug.security import check_password_hash, generate_password_hash
from utils import generar_codigo_2fa  # Importa funciones auxiliares
from models import db
from forms import loginForm, RegistroForm, RegistroForm_adm
from functools import wraps
from flask import jsonify
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)


def verificar_roles(*roles_permitidos):
    def decorador(f):
        @wraps(f)
        def funcion_verificada(*args, **kwargs):
            rol_usuario = session.get('rol', None)
            print(f"Rol del usuario: {rol_usuario}")

            if rol_usuario not in roles_permitidos:
                return render_template('404.html'), 404

            return f(*args, **kwargs)

        return funcion_verificada
    return decorador


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
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify', data=payload)
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
        user.ultimo_login = datetime.now()
        db.session.commit()

        session['id_usuario'] = user.id_usuario
        session['expiracion_sesion'] = (
            datetime.now() + timedelta(seconds=30)).timestamp()

        generar_codigo_2fa(user)

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
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()

        if not result.get('success'):
            flash('Por favor completa el reCAPTCHA.', 'danger')
            return redirect(url_for('auth.registro'))

            # Verificar si el nombre de usuario ya existe en la base de datos
        usuario_existente = usuario.query.filter_by(
            nombre_usuario=form.nombre_usuario.data).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            return redirect(url_for('auth.registro_adm'))

        # Hashear la contraseña antes de almacenarla
        hashed_password = generate_password_hash(form.contrasenia.data)

        user = usuario(
            nombre=form.nombre.data,
            nombre_usuario=form.nombre_usuario.data,
            telefono=form.telefono.data,
            email=form.email.data,
            contrasenia=hashed_password,  # Guardar la contraseña encriptada
            ultimo_login=datetime.utcnow()
        )

        db.session.add(user)
        db.session.commit()

        session['id_usuario'] = user.id_usuario
        session['expiracion_sesion'] = (
            datetime.utcnow() + timedelta(seconds=20)).timestamp()

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
                return redirect(url_for('admin'))
            elif user.rol.lower() == 'produccion':
                return redirect(url_for('produccion'))
            elif user.rol.lower() == 'ventas':
                return redirect(url_for('ventas'))
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
        # Redirigir a la página de verificación
        return redirect(url_for('auth.verificar_codigo_2fa'))
    else:
        flash('Usuario no encontrado. Inicia sesión nuevamente.', 'danger')
        return redirect(url_for('auth.login'))


@auth.route('/perfil', methods=['GET', 'POST'])
@login_required
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


@auth.route('/redirigir')
def redirigir():
    # Obtener el rol del usuario desde la sesión (o de donde lo manejes)
    user = usuario.query.get(session.get('id_usuario'))
    rol = session.get('rol', 'admin')  # Por defecto "cliente"

    # Diccionario con las rutas según el rol
    if user.rol.lower() == 'admin':
        return redirect(url_for('admin'))
    elif user.rol.lower() == 'produccion':
        return redirect(url_for('produccion'))
    elif user.rol.lower() == 'ventas':
        return redirect(url_for('ventas'))
    elif user.rol.lower() == 'cliente':
        return redirect(url_for('cliente'))
    else:
        flash('Rol no reconocido.', 'danger')
        return redirect(url_for('auth.login'))


@auth.route('/registro_adm', methods=['GET', 'POST'])
def registro_adm():
    form = RegistroForm_adm()

    roles_permitidos = ['admin', 'cliente', 'ventas', 'produccion']

    if form.validate_on_submit():

        rol_seleccionado = form.rol.data
        if rol_seleccionado not in roles_permitidos:
            flash('Rol no válido.', 'danger')
            return redirect(url_for('auth.registro_adm'))

            # Verificar si el nombre de usuario ya existe en la base de datos
        usuario_existente = usuario.query.filter_by(
            nombre_usuario=form.nombre_usuario.data).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            return redirect(url_for('auth.registro_adm'))

        # Hashear la contraseña antes de almacenarla
        hashed_password = generate_password_hash(form.contrasenia.data)

        user = usuario(
            nombre=form.nombre.data,
            nombre_usuario=form.nombre_usuario.data,
            telefono=form.telefono.data,
            email=form.email.data,
            contrasenia=hashed_password,  # Guardar la contraseña encriptada
            rol=rol_seleccionado
        )

        db.session.add(user)
        db.session.commit()

        # Autenticar al usuario recién registrado
        login_user(user)

        flash('Usuario registrado y autenticado con éxito!', 'success')
        return render_template('/registro_adm.html', form=form)

    return render_template('/registro_adm.html', form=form)


@auth.route('/expirada')
def expirada():
    expiracion = verificar_expiracion_sesion()
    if expiracion:
        return expiracion  # Redirige al logout si la sesión ha expirado

    return render_template('auth/login.html')


def verificar_expiracion_sesion():
    if 'expiracion_sesion' in session:
        tiempo_expiracion = session['expiracion_sesion']
        tiempo_actual = datetime.now().timestamp()

        if tiempo_actual > tiempo_expiracion:
            flash(
                'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'warning')
            # Llamar a la función logout
            return redirect(url_for('auth.logout'))


@auth.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    """Renderiza la página con la tabla de usuarios, permitiendo búsqueda y filtrado."""
    filtro_rol = request.args.get('rol', '')
    busqueda = request.args.get('q', '')

    query = usuario.query

    if filtro_rol:
        query = query.filter_by(rol=filtro_rol)

    if busqueda:
        query = query.filter(
            (usuario.nombre.ilike(f"%{busqueda}%")) |
            (usuario.nombre_usuario.ilike(f"%{busqueda}%")) |
            (usuario.telefono.ilike(f"%{busqueda}%")) |
            (usuario.email.ilike(f"%{busqueda}%")) |
            (usuario.rol.ilike(f"%{busqueda}%"))
        )

    usuarios = query.all()

    return render_template('registro_adm.html', usuarios=usuarios)


@auth.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    """Elimina un usuario por ID."""
    usuario = usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('auth.registro_adm'))


@auth.route('/obtener_usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    """Obtiene los datos de un usuario específico para edición."""
    usuario = usuario.query.get_or_404(id)
    return render_template('registro_adm.html', usuario=usuario)
