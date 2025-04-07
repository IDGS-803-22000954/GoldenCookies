from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db, Venta, DetalleVenta
from datetime import date
from auth import verificar_roles

pedidos = Blueprint('pedidos', __name__)


@pedidos.route("/pedido", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def pedido():
    forms = forms_ventas.VentaForm(request.form)
    pedidos_hechos = db.session.query(
        Venta).filter(Venta.id_usuario == 3).all()
    return render_template('pedidos.html', pedidos=pedidos_hechos, form=forms)


@pedidos.route("/nuevo_pedido", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def nuevo_pedido():
    forms = forms_ventas.VentaForm(request.form)
    return render_template('nuevo_pedido.html', form=forms, pedidos=session.get('pedidos_acumulados', []))


@pedidos.route("/procesar_t", methods=['POST'])
@verificar_roles('admin', 'cliente')
@login_required
def procesar_t():
    form = forms_ventas.VentaForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        if 'pedidos_acumulados' not in session:
            session['pedidos_acumulados'] = []
        pedidos = session['pedidos_acumulados']

        nueva_venta = {
            "galleta": form.galleta.data,
            "tipo_venta": form.tipo_venta.data,
            "cantidad": form.cantidad.data,
            "precio": form.preciot.data
        }

        flash('ayuda llamen a dios', 'success')
        pedidos.append(nueva_venta)
        session['pedidos_acumulados'] = pedidos

        return redirect(url_for('pedidos.nuevo_pedido'))

    flash("Error al procesar el pedido.", "danger")
    return render_template('nuevo_pedido.html', form=form, pedidos=session.get('pedidos_acumulados', []))


@pedidos.route("/terminar_pedido", methods=['POST', 'GET'])
@verificar_roles('admin', 'cliente')
@login_required
def terminar_pedido():
    session.pop('pedidos_acumulados', None)
    return redirect(url_for('pedidos.pedido'))


@pedidos.route("/eliminar_pedido/<int:indice>", methods=['POST', 'GET'])
@verificar_roles('admin', 'cliente')
@login_required
def eliminar_pedido(indice):
    pe = session['pedidos_acumulados']
    pe.pop(indice)
    session['pedidos_acumulados'] = pe

    return redirect(url_for('pedidos.nuevo_pedido'))


@pedidos.route("/realizar_pedido", methods=['POST', 'GET'])
@verificar_roles('admin', 'cliente')
@login_required
def realizar_pedido():
    pe = session.get('pedidos_acumulados', [])
    if request.method == 'POST':
        try:
            ptotal = sum(float(venta["precio"]) for venta in pe)

            nuevo_pedido = Venta(
                fecha=date.today(),
                tipo_venta='web',
                total=ptotal,
                metodo_pago='efectivo',
                id_usuario=3,
                created_at=date.today(),
                estado='pendiente',
                pagado=0
            )
            db.session.add(nuevo_pedido)
            db.session.flush()

            idv = nuevo_pedido.id_venta
            for v in pe:

                nuevo_detalle = DetalleVenta(
                    cantidad=int(v["cantidad"]),
                    precio_unitario=float(v["precio"]),
                    tipo_venta=v["tipo_venta"],
                    id_venta=idv,
                    created_at=date.today()
                )
                db.session.add(nuevo_detalle)

            db.session.commit()
            flash('Pedido realizado con éxito', 'success')
            return redirect(url_for('pedidos.terminar_pedido'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al realizar el pedido: {str(e)}', 'danger')
    return redirect(url_for('pedidos.pedido'))


@pedidos.route("/detalles_pedido/<int:id_venta>", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def detalles_pedido(id_venta):
    pedidoss = db.session.query(DetalleVenta).filter(
        DetalleVenta.id_venta == id_venta).all()
    return render_template('detalles_pedido.html', pedidos=pedidoss)
