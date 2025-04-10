from recetas.recetas import calcular_precio_galleta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, Insumo, Proveedor, LoteInsumo, CompraInsumo, Receta, RecetaInsumo, Galleta
from forms_compras import CompraInsumoForm
from datetime import datetime
from flask_login import login_required, current_user
from auth import verificar_roles

compras_bp = Blueprint('compras_bp', __name__, template_folder='templates')

# Importar la función de cálculo de precio de recetas.py


def actualizar_precios_galletas(id_insumo):
    """
    Actualiza los precios de todas las galletas que utilizan un insumo específico.
    """
    # Encontrar todas las recetas que usan este insumo
    recetas_insumos = RecetaInsumo.query.filter_by(id_insumo=id_insumo).all()

    # Recopilar los IDs únicos de recetas
    ids_recetas = set(ri.id_receta for ri in recetas_insumos)

    # Obtener todas las recetas afectadas
    recetas = Receta.query.filter(Receta.id_receta.in_(ids_recetas)).all()

    # Para cada receta, actualizar el precio de su galleta
    for receta in recetas:
        galleta = Galleta.query.get(receta.id_galleta)
        if galleta:
            nuevo_precio = calcular_precio_galleta(galleta.id_galleta)
            galleta.precio = nuevo_precio

    # Guardar todos los cambios
    db.session.commit()


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

    compras = CompraInsumo.query.join(
        LoteInsumo).join(Insumo).join(Proveedor).all()

    if form.validate_on_submit():
        try:
            # (presentaciones * peso unitario)
            cantidad_total = form.cantidad_presentaciones.data * form.peso_unitario.data

            # (precio_total / cantidad_total)
            precio_unitario = form.precio_total.data / cantidad_total

            id_insumo = form.id_insumo.data

            lote = LoteInsumo(
                cantidad=cantidad_total,
                cantidad_disponible=cantidad_total,
                costo_total=form.precio_total.data,
                fecha_caducidad=form.fecha_caducidad.data,
                id_insumo=id_insumo
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

            insumo = Insumo.query.get(id_insumo)
            insumo.cantidad_insumo += cantidad_total

            db.session.commit()

            # Después de registrar la compra, actualizar los precios de las galletas
            actualizar_precios_galletas(id_insumo)

            flash(
                'Compra registrada y precios de galletas actualizados exitosamente!', 'success')
            return redirect(url_for('compras_bp.listar_compras'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'danger')

    return render_template('compras.html', form=form, compras=compras)
