from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from models import usuario
from werkzeug.security import check_password_hash, generate_password_hash
from models import db
from forms import loginForm, RegistroForm, RegistroForm_adm
from functools import wraps
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
        nombre_usuario = form.username.data
        contrasenia = form.password.data

        user = usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if not user:
            flash('El usuario no existe. Regístrate primero.', 'warning')
            return redirect(url_for('auth.login'))

        if user.bloqueado:
            flash('Tu cuenta está bloqueada. Contacta al soporte.', 'danger')
            return redirect(url_for('auth.login'))

        if not check_password_hash(user.contrasenia, contrasenia):
            user.intentos_fallidos += 1
            if user.intentos_fallidos >= 5:
                user.bloqueado = True
                flash('Cuenta bloqueada por intentos fallidos.', 'danger')
            db.session.commit()
            return redirect(url_for('auth.login'))

        # Restablecer intentos fallidos
        user.intentos_fallidos = 0
        user.ultimo_login = datetime.now()
        db.session.commit()

        # Iniciar sesión directamente
        login_user(user)

        session['id_usuario'] = user.id_usuario
        session['expiracion_sesion'] = (
            datetime.now() + timedelta(seconds=30)).timestamp()
        session['rol'] = user.rol.lower()

        # Redirigir según el rol del usuario
        if user.rol.lower() == 'admin':
            return redirect(url_for('admin'))
        elif user.rol.lower() == 'produccion':
            return redirect(url_for('produccion.index'))
        elif user.rol.lower() == 'ventas':
            return redirect(url_for('venta.ventas'))
        elif user.rol.lower() == 'cliente':
            return redirect(url_for('cliente'))
        else:
            flash('Rol no reconocido.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form)


@auth.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()

    if form.validate_on_submit():
        # Verificar si el nombre de usuario ya existe en la base de datos
        usuario_existente = usuario.query.filter_by(
            nombre_usuario=form.nombre_usuario.data).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            return redirect(url_for('auth.registro'))

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
        session['rol'] = user.rol.lower()

        # Autenticar al usuario recién registrado
        login_user(user)

        flash('Usuario registrado y autenticado con éxito!', 'success')
        return redirect(url_for('cliente'))  # Redirigir al menú

    return render_template('auth/registro.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()  # Cierra la sesión
    flash("Has cerrado sesión exitosamente", "success")  # Mensaje opcional
    session.pop('id_usuario', None)  # Elimina el ID de usuario de la sesión
    session.pop('rol', None)
    session.pop('expiracion_sesion', None)  # Elimina la expiración de sesión
    return redirect('/catalogo')


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
        return redirect(url_for('venta.ventas'))
    elif user.rol.lower() == 'cliente':
        return redirect(url_for('cliente'))
    else:
        flash('Rol no reconocido.', 'danger')
        return redirect(url_for('auth.login'))


@auth.route('/registro_adm', methods=['GET', 'POST'])
@login_required
@verificar_roles('admin')
def registro_adm():
    form = RegistroForm_adm()

    # Obtener lista de usuarios con filtrado si existe
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

    # Obtener todos los usuarios según los filtros
    usuarios_lista = query.all()

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

        nuevo_usuario = usuario(
            nombre=form.nombre.data,
            nombre_usuario=form.nombre_usuario.data,
            telefono=form.telefono.data,
            email=form.email.data,
            contrasenia=hashed_password,  # Guardar la contraseña encriptada
            rol=rol_seleccionado
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario registrado con éxito!', 'success')
        return redirect(url_for('auth.registro_adm'))

    return render_template('/registro_adm.html', form=form, usuarios=usuarios_lista)


@auth.route('/actualizar_usuario', methods=['POST'])
@login_required
@verificar_roles('admin')
def actualizar_usuario():
    user_id = request.form.get('userId')

    if not user_id:
        flash('ID de usuario no proporcionado.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    # Buscar el usuario existente
    user_to_update = usuario.query.get(int(user_id))

    if not user_to_update:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    # Proteger a los usuarios admin de ser modificados
    if user_to_update.rol == 'admin':
        flash('No se pueden modificar usuarios con rol de administrador.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    # Verificar que el nombre de usuario no esté siendo usado por otro usuario
    nombre_usuario = request.form.get('nombre_usuario')
    nombre_usuario_existente = usuario.query.filter(
        usuario.nombre_usuario == nombre_usuario,
        usuario.id_usuario != int(user_id)
    ).first()

    if nombre_usuario_existente:
        flash('El nombre de usuario ya está en uso por otro usuario.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    # Actualizar los datos del usuario
    user_to_update.nombre = request.form.get('nombre')
    user_to_update.nombre_usuario = nombre_usuario
    user_to_update.telefono = request.form.get('telefono')
    user_to_update.email = request.form.get('email')
    user_to_update.rol = request.form.get('rol')

    # Asegurarse de que no se pueda cambiar a rol admin
    if user_to_update.rol == 'admin':
        flash('No se puede cambiar el rol a administrador.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    # Actualizar contraseña solo si se proporciona una nueva
    nueva_contrasenia = request.form.get('contrasenia')
    if nueva_contrasenia and nueva_contrasenia.strip():
        user_to_update.contrasenia = generate_password_hash(nueva_contrasenia)

    db.session.commit()
    flash('Usuario actualizado con éxito!', 'success')
    return redirect(url_for('auth.registro_adm'))


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

    return render_template('registro_adm.html', usuario=usuarios)


@auth.route('/eliminar_usuario/<int:id>', methods=['POST'])
@login_required
@verificar_roles('admin')
def eliminar_usuario(id):
    """Elimina un usuario por ID."""
    user = usuario.query.get_or_404(id)

    # Proteger a los usuarios admin de ser eliminados
    if user.rol == 'admin':
        flash('No se pueden eliminar usuarios con rol de administrador.', 'danger')
        return redirect(url_for('auth.registro_adm'))

    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('auth.registro_adm'))


@auth.route('/obtener_usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    """Obtiene los datos de un usuario específico para edición."""
    usuario = usuario.query.get_or_404(id)
    return render_template('registro_adm.html', usuario=usuario)
