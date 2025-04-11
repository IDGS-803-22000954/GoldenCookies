from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db, Receta, RecetaInsumo, CompraInsumo, Galleta, Insumo
from flask import session
from flask import g
from recetas.forms_recetas import RecetaForm, RecetaInsumoForm
from flask import g
from flask import current_app
from werkzeug.utils import secure_filename
import os
from flask import jsonify
from flask_login import login_required
from auth import verificar_roles

recetas_bp = Blueprint('recetas', __name__, url_prefix='/recetas')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calcular_precio_galleta(id_galleta):
    receta = Receta.query.filter_by(id_galleta=id_galleta).first()
    if not receta:
        return 0.0

    insumos_receta = RecetaInsumo.query.filter_by(
        id_receta=receta.id_receta).all()
    costo_total = 0.0

    for ri in insumos_receta:
        insumo = Insumo.query.get(ri.id_insumo)

        compra = (
            CompraInsumo.query
            .join(CompraInsumo.lote_insumo)
            .filter(CompraInsumo.lote_insumo.has(id_insumo=insumo.id_insumo))
            .order_by(CompraInsumo.created_at.desc())
            .first()
        )

        if not compra:
            continue

        precio_unitario = compra.precio_unitario
        cantidad_usada = ri.cantidad_insumo

        costo_insumo = cantidad_usada * precio_unitario
        costo_total += costo_insumo

    if receta.cantidad_produccion == 0:
        return 0.0

    precio_unitario_galleta = (costo_total / receta.cantidad_produccion) * 1.75
    precio = round(precio_unitario_galleta, 2)
    return precio


@recetas_bp.route("/", methods=['GET', 'POST'])
@login_required
@verificar_roles('admin','produccion')
def receta():
    form = RecetaForm()
    form.cargar_opciones()

    if request.method == 'POST':
        return insertar_receta(form)

    recetas = Receta.query.all()
    insumos = Insumo.query.all()
    galletas = Galleta.query.all()

    return render_template('recetas.html', form=form, recetas=recetas, insumos=insumos, galletas=galletas)


@recetas_bp.route('/insertar_receta', methods=['GET', 'POST'])
@login_required
@verificar_roles('admin','produccion')
def insertar_receta():
    form = RecetaForm()
    form.cargar_opciones()

    if request.method == 'POST':
        nombre = form.nombre.data
        detalles = form.detalles.data
        cantidad_produccion = form.cantidad_produccion.data
        peso_unidad = form.peso_unidad.data
        descripcion = form.descripcion.data
        imagen_file = form.imagen_galleta.data

        nombre_imagen = None
        if imagen_file:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagen_file.stream.seek(0)
            nuevo_nombre = secure_filename(imagen_file.filename)
            ruta_img = os.path.join(upload_folder, nuevo_nombre)
            imagen_file.save(ruta_img)
            nombre_imagen = nuevo_nombre

        nueva_galleta = Galleta(
            nombre=nombre,
            precio=0.0,
            cantidad_galletas=0,
            descripcion=descripcion,
            peso_unidad=peso_unidad,
            imagen=nombre_imagen
        )
        db.session.add(nueva_galleta)
        db.session.commit()

        nueva_receta = Receta(
            nombre=nombre,
            detalles=detalles,
            cantidad_produccion=cantidad_produccion,
            id_galleta=nueva_galleta.id_galleta
        )
        db.session.add(nueva_receta)
        db.session.commit()

        for insumo in Insumo.query.all():
            insumo_id = insumo.id_insumo
            if f'insumo_{insumo_id}' in request.form:
                try:
                    cantidad = float(
                        request.form[f'cantidad_{insumo_id}'].replace(',', '.'))
                except ValueError:
                    cantidad = 0.0

                if cantidad > 0:
                    receta_insumo = RecetaInsumo(
                        id_receta=nueva_receta.id_receta,
                        id_insumo=insumo_id,
                        cantidad_insumo=cantidad
                    )
                    db.session.add(receta_insumo)

        db.session.commit()

        nueva_galleta.precio = calcular_precio_galleta(
            nueva_galleta.id_galleta)
        db.session.commit()

        flash("Receta y galleta agregadas con éxito", "success")
        return redirect(url_for('recetas.receta'))

    return redirect(url_for('recetas.receta'))


@recetas_bp.route('/modificar/<int:id_receta>', methods=['GET', 'POST'])
@login_required
@verificar_roles('admin','produccion')
def modificar_receta(id_receta):
    receta = Receta.query.get_or_404(id_receta)
    galleta = Galleta.query.get_or_404(receta.id_galleta)
    insumos = Insumo.query.all()

    if request.method == 'POST':
        receta.nombre = request.form.get('nombre')
        receta.detalles = request.form.get('detalles')
        receta.cantidad_produccion = int(
            request.form.get('cantidad_produccion'))

        galleta.nombre = receta.nombre
        galleta.descripcion = galleta.descripcion
        galleta.peso_unidad = float(request.form.get('peso_unidad') or 0)

        imagen_file = request.files.get('imagen_galleta')
        if imagen_file and imagen_file.filename != '':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            imagen_file.stream.seek(0)
            nuevo_nombre = secure_filename(imagen_file.filename)
            ruta_img = os.path.join(upload_folder, nuevo_nombre)
            imagen_file.save(ruta_img)
            galleta.imagen = nuevo_nombre

        db.session.commit()

        RecetaInsumo.query.filter_by(id_receta=receta.id_receta).delete()
        db.session.commit()

        for insumo in insumos:
            insumo_id = insumo.id_insumo
            if f'insumo_{insumo_id}' in request.form:
                try:
                    cantidad = float(
                        request.form[f'cantidad_{insumo_id}'].replace(',', '.'))
                except ValueError:
                    cantidad = 0.0

                if cantidad > 0:
                    nueva_ri = RecetaInsumo(
                        id_receta=receta.id_receta,
                        id_insumo=insumo_id,
                        cantidad_insumo=cantidad
                    )
                    db.session.add(nueva_ri)

        db.session.commit()

        galleta.precio = calcular_precio_galleta(galleta.id_galleta)
        db.session.commit()

        flash("Receta y galleta modificadas correctamente", "success")
        return redirect(url_for('recetas.receta'))

    receta_insumos = {
        ri.id_insumo: ri.cantidad_insumo for ri in receta.receta_insumo}

    insumos_data = [
        {
            'id_insumo': insumo.id_insumo,
            'nombre': insumo.nombre,
            'unidad_medida': insumo.unidad_medida,
            'cantidad': receta_insumos.get(insumo.id_insumo, 0)
        }
        for insumo in insumos
    ]

    return jsonify({
        'receta': {
            'id': receta.id_receta,
            'nombre': receta.nombre,
            'detalles': receta.detalles,
            'cantidad_produccion': receta.cantidad_produccion
        },
        'galleta': {
            'nombre': galleta.nombre,
            'descripcion': galleta.descripcion,
            'peso_unidad': galleta.peso_unidad,
            'imagen': galleta.imagen
        },
        'insumos': insumos_data
    })
