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
    
    # Los select fields
    form.id_insumo.choices = [(i.id_insumo, f"{i.nombre} ({i.unidad_medida})") 
                             for i in Insumo.query.filter(Insumo.id_insumo != 0).order_by(Insumo.nombre)]
    form.id_proveedor.choices = [(p.id_proveedor, p.nombre) 
                                for p in Proveedor.query.filter(Proveedor.estatus != 0).order_by(Proveedor.nombre)]
    
    compras = CompraInsumo.query.join(LoteInsumo).join(Insumo).join(Proveedor).all()

    if form.validate_on_submit():
        try:
            #(presentaciones * peso unitario)
            cantidad_total = form.cantidad_presentaciones.data * form.peso_unitario.data
            
            #(precio_total / cantidad_total)
            precio_unitario = form.precio_total.data / cantidad_total
            

            lote = LoteInsumo(
                cantidad=cantidad_total,
                cantidad_disponible=cantidad_total,
                costo_total=form.precio_total.data,
                fecha_caducidad=form.fecha_caducidad.data,
                id_insumo=form.id_insumo.data
            )
            db.session.add(lote)
            db.session.flush()

            compra = CompraInsumo(
                presentacion=form.presentacion.data,
                cantidad_presentaciones=form.cantidad_presentaciones.data,
                precio_unitario=precio_unitario,
                precio_total=form.precio_total.data,
                id_proveedor=form.id_proveedor.data,
                id_lote_insumo=lote.id_lote_insumo
            )
            db.session.add(compra)


            insumo = Insumo.query.get(form.id_insumo.data)
            insumo.cantidad_insumo += cantidad_total

            db.session.commit()
            flash('Compra registrada exitosamente!', 'success')
            return redirect(url_for('compras_bp.listar_compras'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'danger')

    return render_template('compras.html', form=form, compras=compras)