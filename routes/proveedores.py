from flask import Blueprint, Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, Proveedor, db
from forms_compras import InsumoForm, ProveedorForm
from flask_login import login_required
from auth import verificar_roles


proveedor_bp = Blueprint('proveedor_bp', __name__, url_prefix='/proveedor_bp')


@proveedor_bp.route("/proveedores", methods=['GET', 'POST'])
@verificar_roles('admin')
@login_required
def agregarProveedor():
    formulario = ProveedorForm()  # Cambiado a ProveedorForm
    proveedores = Proveedor.query.all()
    
    if formulario.validate_on_submit():
        nuevo_proveedor = Proveedor(
            nombre=formulario.nombre.data,  # Cambiado a nombre
            contacto=formulario.contacto.data,
            telefono=formulario.telefono.data
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        flash('Proveedor agregado correctamente', 'success')
        return redirect(url_for('proveedor_bp.agregarProveedor'))  # Corregido el nombre de la función
    
    return render_template('proovedores.html', formulario=formulario, proveedores=proveedores)


@proveedor_bp.route("/editar_proveedor", methods=['POST'])
def editar_proveedor():
    id_proveedor = request.form.get('id_proveedor')
    print(f"ID Proveedor recibido: {id_proveedor}")
    nombre = request.form.get('nombre')
    contacto = request.form.get('contacto')
    telefono = request.form.get('telefono')
    
    proveedor = Proveedor.query.get_or_404(id_proveedor)
    
    proveedor.nombre = nombre
    proveedor.contacto = contacto
    proveedor.telefono = telefono
    
    db.session.commit()
    flash('Proveedor actualizado correctamente!', 'success')
    return redirect(url_for('proveedor_bp.agregarProveedor'))


@proveedor_bp.route("/cambiar_estatus/<int:id>")
def cambiar_estatus(id):
    try:
        proveedor = Proveedor.query.get_or_404(id)
        proveedor.estatus = not proveedor.estatus
        
        db.session.commit()
        action = "reactivado" if proveedor.estatus else "desactivado"
        flash(f'Proveedor {action} correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al cambiar estatus', 'error')
    
    return redirect(url_for('proveedor_bp.agregarProveedor'))