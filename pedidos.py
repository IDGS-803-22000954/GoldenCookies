from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db, Venta, DetalleVenta, Galleta
from datetime import date
from auth import verificar_roles

pedidos = Blueprint('pedidos', __name__)

@pedidos.route("/catalogo", methods=['GET', 'POST'])
def catalogo():
    if 'pedidos_acumulados' not in session:
        session['pedidos_acumulados'] = []
    forms = forms_ventas.VentaForm(request.form)
    usuario=session.get('id_usuario')
    galletas=db.session.query(Galleta)
    return render_template('Main.html', usuario=usuario, galletas=galletas, form=forms)

@pedidos.route("/pedido", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def pedido():
    forms = forms_ventas.VentaForm(request.form)
    pedidos_hechos = db.session.query(Venta).filter(Venta.id_usuario == session.get('id_usuario')).all()
    return render_template('pedidos.html', pedidos=pedidos_hechos, form=forms)


@pedidos.route("/carrito", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def carrito():
    if 'pedidos_acumulados' not in session:
        session['pedidos_acumulados'] = []
    forms = forms_ventas.VentaForm(request.form)
    galletas = session['pedidos_acumulados']
    ptotal = sum(float(galleta["precio"]) for galleta in galletas)
    print(session)
    return render_template('carrito.html', galletas=galletas, ptotal=ptotal, form=forms)


@pedidos.route("/procesar_t", methods=['POST', 'GET'])
@verificar_roles('admin', 'cliente')
@login_required
def procesar_t():
    form = forms_ventas.VentaForm(request.form)
    if request.method == 'POST':
        cantidad=form.cantidad.data

        galleta = db.session.query(Galleta).filter_by(id_galleta=form.galleta.data).first()
        cantidad = galleta.cantidad_galletas
        c=form.cantidad.data
        if c > cantidad:
            flash(f"No hay suficientes galletas disponibles para '{galleta.nombre}'",'danger') 
        else: 
        
            if 'pedidos_acumulados' not in session:
                session['pedidos_acumulados'] = []
            pedidos = session['pedidos_acumulados']

            nueva_venta = {
                "id_galleta": galleta.id_galleta,
                "galleta": galleta.nombre,
                "imagen": galleta.imagen,
                "tipo_venta": form.tipo_venta.data,
                "cantidad": form.cantidad.data,
                "precio": int(c)*int(galleta.precio)
            }

            pedidos.append(nueva_venta)
            session['pedidos_acumulados'] = pedidos
            flash("Producto añadido al carrito con éxito", 'success')

        return redirect(url_for('pedidos.catalogo'))

    flash("Error al procesar el pedido.", "danger")
    return redirect(url_for('pedidos.catalogo'))


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

    return redirect(url_for('pedidos.carrito'))


@pedidos.route("/realizar_pedido", methods=['POST', 'GET'])
@verificar_roles('admin', 'cliente')
@login_required
def realizar_pedido():
    pe = session.get('pedidos_acumulados', [])
    if request.method == 'POST':
        try:
            ptotal = sum(float(venta["precio"]) for venta in pe)

            quantities = {}
            for item in pe:
                id_galleta = item["id_galleta"]
                if id_galleta not in quantities:
                    quantities[id_galleta] = 0
                quantities[id_galleta] += item["cantidad"]

            for id_galleta, total_quantity in quantities.items():
                galleta = db.session.query(Galleta).filter_by(id_galleta=id_galleta).first()
                if galleta:
                    if total_quantity > galleta.cantidad_galletas:
                        flash(f"No hay suficientes galletas disponibles para '{galleta.nombre}'. "
                              f"Stock disponible: {galleta.cantidad_galletas}. Intentaste comprar: {total_quantity}",
                              'warning')
                        return redirect(url_for('pedidos.carrito'))

            nuevo_pedido = Venta(
                tipo_venta='pedido',
                total=ptotal,
                id_usuario=session.get('id_usuario'),
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
                    tipo_venta='unidad',
                    id_venta=idv,
                    id_galleta=int(v['id_galleta']),
                    created_at=date.today()
                )
                db.session.add(nuevo_detalle)

            db.session.commit()
            flash('Pedido realizado con éxito', 'success')
            session.pop('pedidos_acumulados', None)
            return redirect(url_for('pedidos.carrito'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al realizar el pedido: {str(e)}', 'danger')
    return redirect(url_for('pedidos.carrito'))

@pedidos.route("/detalles_pedido/<int:id_venta>", methods=['GET', 'POST'])
@verificar_roles('admin', 'cliente')
@login_required
def detalles_pedido(id_venta):
    pedidoss = db.session.query(DetalleVenta).filter(DetalleVenta.id_venta == id_venta).join(Galleta).all()
    print(pedidoss)
    return render_template('detalles_pedido.html', pedidos=pedidoss)
