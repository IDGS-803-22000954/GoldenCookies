from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db, Venta, DetalleVenta, usuario, Galleta
from datetime import date
from auth import verificar_roles

venta = Blueprint('venta', __name__)


@venta.route("/ventas", methods=['GET', 'POST'])
@verificar_roles('admin', 'ventas')
@login_required
def ventas():
    ventas_acumuladas = session.get('ventas_acumuladas', [])
    forms = forms_ventas.VentaForm(request.form)
    galletas = db.session.query(Galleta)
    return render_template('venta.html', ventas=ventas_acumuladas, form=forms, galletas=galletas)


@venta.route("/procesar_tabla", methods=['POST'])
@verificar_roles('admin', 'ventas')
@login_required
def procesar_tabla():
    form = forms_ventas.VentaForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        galleta = db.session.query(Galleta).filter_by(id_galleta=form.galleta.data).first()
        cantidad = galleta.cantidad_galletas
        c=form.cantidad.data
        if c > cantidad:
            flash(f"No hay suficientes galletas disponibles para '{galleta.nombre}'",'danger') 
        else: 
            if 'ventas_acumuladas' not in session:
                session['ventas_acumuladas'] = []
            ventas = session['ventas_acumuladas']

            nueva_venta = {
                "id_galleta":galleta.id_galleta,
                "galleta": galleta.nombre,
                "tipo_venta": form.tipo_venta.data,
                "cantidad": form.cantidad.data,
                "precio":int(c)*int(galleta.precio_sugerido)
            }

            ventas.append(nueva_venta)
            session['ventas_acumuladas'] = ventas
            return redirect(url_for('venta.ventas'))
    else:
        flash("Error al procesar la venta.", "danger")
    return redirect(url_for('venta.ventas'))


@venta.route("/terminar_venta", methods=['POST', 'GET'])
@verificar_roles('admin', 'ventas')
@login_required
def terminar_venta():
    session.pop('ventas_acumuladas', None)
    return redirect(url_for('venta.ventas'))


@venta.route("/eliminar_venta/<int:indice>", methods=['POST', 'GET'])
def eliminar_venta(indice):
    va = session['ventas_acumuladas']
    if request.method == 'POST':
        va.pop(indice)
    session['ventas_acumuladas'] = va

    return redirect(url_for('venta.ventas'))


@venta.route("/realizar_venta", methods=['POST', 'GET'])
@verificar_roles('admin', 'ventas')
@login_required
def realizar_venta():
    va = session.get('ventas_acumuladas', [])
    if request.method == 'POST' and va:
        try:
            ptotal = sum(float(venta["precio"]) for venta in va)

            nueva_venta = Venta(
                fecha=date.today(),
                tipo_venta='local',
                total=ptotal,
                metodo_pago='efectivo',
                id_usuario=session.get('id_usuario'),
                created_at=date.today(),
                fecha_recogida=date.today(),
                pagado=1
            )
            db.session.add(nueva_venta)
            db.session.flush()

            idv = nueva_venta.id_venta
            for v in va:
                galleta = db.session.query(Galleta).filter_by(id_galleta=v["id_galleta"]).first()
                if galleta:
                    if galleta.cantidad_galletas >= int(v["cantidad"]):
                        galleta.cantidad_galletas -= int(v["cantidad"])
                    else:
                        flash(f"No hay suficientes galletas disponibles para '{galleta.nombre}'", 'warning')
                        db.session.rollback()
                        return redirect(url_for('venta.ventas'))
                nuevo_detalle = DetalleVenta(
                    cantidad=int(v["cantidad"]),
                    precio_unitario=float(v["precio"]),
                    tipo_venta=v["tipo_venta"],
                    id_venta=idv,
                    created_at=date.today()
                )
                db.session.add(nuevo_detalle)
        
            db.session.commit()
            flash('Venta realizada con éxito', 'success')
            session.pop('ventas_acumuladas', None)
            return redirect(url_for('venta.ventas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al realizar la venta', 'danger')
    flash('No se puede hacer una venta sin galletas', 'danger')
    return redirect(url_for('venta.ventas'))


@venta.route("/venta_pedido", methods=['GET', 'POST'])
@verificar_roles('admin', 'ventas')
@login_required
def venta_pedido():
    pedidos = db.session.query(Venta).filter(
        Venta.estado == 'pendiente').join(usuario).all()
    return render_template('venta_pedido.html', pedidos=pedidos)


@venta.route("/realizar_venta_pedido/<int:id_venta>", methods=['GET', 'POST'])
@verificar_roles('admin', 'ventas')
@login_required
def realizar_venta_pedido(id_venta):
    venta = db.session.query(Venta).filter_by(id_venta=id_venta).first()
    if request.method == 'POST':
        venta.estado = 'lista'
        venta.fecha_recogida = date.today()
        venta.pagado = 1
        
    return redirect(url_for('venta.venta_pedido'))


