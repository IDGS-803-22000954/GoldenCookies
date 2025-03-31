from flask import Blueprint, Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, Proveedor, db
from forms_compras import InsumoForm

insumo_bp = Blueprint('insumo_bp', __name__, url_prefix='/insumo_bp')



@insumo_bp.route("/insumo", methods=['GET', 'POST'])
def agregarInsumo():
    formulario = InsumoForm()
    insumos = Insumo.query.all()  # Consulta todos los registros de la tabla Insumo
    
    if formulario.validate_on_submit():
        nuevo_insumo = Insumo(
            nombre=formulario.nombre.data,
            unidad_medida=formulario.unidad_medida.data,
            cantidad_insumo=formulario.cantidad_insumo.data
        )
        db.session.add(nuevo_insumo)
        db.session.commit()
        flash('Insumo agregado correctamente!', 'success')
        return redirect(url_for('insumo_bp.agregarInsumo'))
    
    return render_template('insumo.html', formulario=formulario, insumos=insumos)


@insumo_bp.route("/editar_insumo", methods=['POST'])
def editar_insumo():
    id_insumo = request.form.get('id_insumo')
    nombre = request.form.get('nombre')
    unidad_medida = request.form.get('unidad_medida')
    cantidad_insumo = request.form.get('cantidad_insumo')
    
    insumo = Insumo.query.get_or_404(id_insumo)
    
    insumo.nombre = nombre
    insumo.unidad_medida = unidad_medida
    insumo.cantidad_insumo = cantidad_insumo
    
    db.session.commit()
    flash('Insumo actualizado correctamente!', 'success')
    return redirect(url_for('insumo_bp.agregarInsumo'))
