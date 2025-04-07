from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, Insumo, Proveedor, LoteInsumo, CompraInsumo
from forms_compras import CompraInsumoForm
from datetime import datetime
from flask_login import login_required, current_user
from auth import verificar_roles

compras_bp = Blueprint('compras_bp', __name__, template_folder='templates')


@compras_bp.route('/compras', methods=['GET', 'POST'])
@verificar_roles('admin', 'produccion')
@login_required
def listar_compras():
    form = CompraInsumoForm()
    compras = CompraInsumo.query.join(
        LoteInsumo).join(Insumo).join(Proveedor).all()
    # Llenar los select fields
    form.id_insumo.choices = [(i.id_insumo, i.nombre) for i in Insumo.query.filter(
        Insumo.id_insumo != 0).order_by(Insumo.nombre)]
    form.id_proveedor.choices = [(p.id_proveedor, p.nombre) for p in Proveedor.query.filter(
        Proveedor.estatus != 0).order_by(Proveedor.nombre)]

    if form.validate_on_submit():
        try:

            lote = LoteInsumo(
                cantidad=form.cantidad.data,
                cantidad_disponible=form.cantidad.data,
                costo_unitario=form.costo_unitario.data,
                fecha_compra=form.fecha_compra.data,
                fecha_caducidad=form.fecha_caducidad.data,
                id_insumo=form.id_insumo.data
            )
            db.session.add(lote)
            db.session.flush()

            compra = CompraInsumo(
                presentacion=form.presentacion.data,
                cantidad_normalizada=form.cantidad.data,
                precio_total=form.cantidad.data * form.costo_unitario.data,
                id_proveedor=form.id_proveedor.data,
                id_lote_insumo=lote.id_lote_insumo
            )
            db.session.add(compra)

            insumo = Insumo.query.get(form.id_insumo.data)
            insumo.cantidad_insumo += form.cantidad.data

            db.session.commit()

            flash('Compra registrada exitosamente!', 'success')
            return redirect(url_for('compras_bp.listar_compras'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'danger')

    return render_template('compras.html', form=form, compras=compras)
