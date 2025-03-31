from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db, Receta, RecetaInsumo, Insumo, Galleta
from flask import session
from flask import g
from recetas.forms_recetas import RecetaForm, RecetaInsumoForm
from flask import g
from flask import jsonify



recetas_bp = Blueprint('recetas', __name__, url_prefix='/recetas')

@recetas_bp.route("/", methods=['GET', 'POST'])
def receta():
    form = RecetaForm()
    form.cargar_opciones()  # Instancia del formulario
    if request.method == 'POST':
        return insertar_receta()  # Llama a la función de inserción

    insumos = Insumo.query.all()
    galletas = Galleta.query.all()
    recetas = Receta.query.options(db.joinedload(Receta.receta_insumo)).all()

    return render_template('recetas.html', form=form, insumos=insumos, galletas=galletas, recetas=recetas)


@recetas_bp.route('/insertar_receta', methods=['GET', 'POST'])
def insertar_receta():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad_produccion = request.form.get('cantidad_produccion')
    id_galleta = request.form.get('id_galleta')

    if not nombre or not id_galleta:
        flash("El nombre y la galleta son obligatorios", "danger")
        return redirect(url_for('recetas.receta'))

    nueva_receta = Receta(
        nombre=nombre,
        descripcion=descripcion,
        cantidad_produccion=cantidad_produccion,
        id_galleta=id_galleta
    )
    db.session.add(nueva_receta)
    db.session.commit()

    
    for insumo_id in request.form:
        if insumo_id.startswith('insumo_'):
            id_insumo = int(insumo_id.split('_')[1])
            
            try:
                cantidad_insumo = float(request.form[f'cantidad_{id_insumo}'].replace(',', '.'))
            except ValueError:
                cantidad_insumo = 0.0
            
            if cantidad_insumo > 0:
                receta_insumo = RecetaInsumo(
                    id_receta=nueva_receta.id_receta,  
                    id_insumo=id_insumo,
                    cantidad_insumo=cantidad_insumo
                )
                db.session.add(receta_insumo)

    db.session.commit()
    flash('Receta agregada con éxito', 'success')
    return redirect(url_for('recetas.receta'))


@recetas_bp.route('/modificar_receta/<int:id_receta>', methods=['GET', 'POST'])
def modificar_receta(id_receta):
    if request.method == 'GET':
        receta = Receta.query.get_or_404(id_receta)
        return jsonify({
            'nombre': receta.nombre,
            'descripcion': receta.descripcion,
            'cantidad_produccion': receta.cantidad_produccion,
            'id_galleta': receta.id_galleta,
            'insumos': [
                {
                    'id_insumo': ri.id_insumo,
                    'nombre': ri.insumo.nombre,
                    'cantidad': ri.cantidad_insumo,
                    'unidad_medida': ri.insumo.unidad_medida
                }
                for ri in receta.receta_insumo
            ]
        })

    # Manejo de la modificación de la receta
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad_produccion = request.form.get('cantidad_produccion')
    id_galleta = request.form.get('id_galleta')

    if not nombre or not id_galleta:
        flash("El nombre y la galleta son obligatorios", "danger")
        return redirect(url_for('recetas.receta'))

    receta = Receta.query.get_or_404(id_receta)
    receta.nombre = nombre
    receta.descripcion = descripcion
    receta.cantidad_produccion = cantidad_produccion
    receta.id_galleta = id_galleta

    # Eliminar insumos existentes
    RecetaInsumo.query.filter_by(id_receta=id_receta).delete()

    # Agregar nuevos insumos
    for insumo_id in request.form:
        if insumo_id.startswith('insumo_'):
            id_insumo = int(insumo_id.split('_')[1])
            cantidad_insumo = float(request.form.get(f'cantidad_{id_insumo}', '0').replace(',', '.'))
            nuevo_insumo = RecetaInsumo(id_receta=id_receta, id_insumo=id_insumo, cantidad_insumo=cantidad_insumo)
            db.session.add(nuevo_insumo)

    db.session.commit()
    flash('Receta modificada con éxito', 'info')
    return redirect(url_for('recetas.receta'))



