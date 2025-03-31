from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db, Venta, DetalleVenta, usuario
from datetime import date

venta = Blueprint('venta', __name__)

@venta.route("/ventas", methods=['GET', 'POST'])
def ventas():
    ventas_acumuladas=session.get('ventas_acumuladas',[])
    forms=forms_ventas.VentaForm(request.form)
    return render_template('venta.html', ventas=ventas_acumuladas, form=forms)

@venta.route("/procesar_tabla", methods=['POST'])
def procesar_tabla():
    form = forms_ventas.VentaForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        if 'ventas_acumuladas' not in session:
            session['ventas_acumuladas'] = []
        ventas = session['ventas_acumuladas']

        nueva_venta = {
            "galleta": form.galleta.data,
            "tipo_venta": form.tipo_venta.data,
            "cantidad": form.cantidad.data,
            "precio": form.preciot.data
        }
        
        ventas.append(nueva_venta)
        print(ventas)
        session['ventas_acumuladas'] = ventas
        return redirect(url_for('venta.ventas'))

    flash("Error al procesar la venta.", "danger")
    return redirect(url_for('venta.ventas'))

@venta.route("/terminar_venta", methods=['POST','GET'])
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
def realizar_venta():
    va = session.get('ventas_acumuladas', [])
    if request.method == 'POST':
        try:
            ptotal = sum(float(venta["precio"]) for venta in va)
            
            nueva_venta = Venta(
                fecha=date.today(),
                tipo_venta='local',
                total=ptotal,
                metodo_pago='efectivo',
                id_usuario=1,
                created_at=date.today(),
                fecha_recogida=date.today(),
                pagado=1
            )
            db.session.add(nueva_venta)
            db.session.flush()
            
            idv = nueva_venta.id_venta
            for v in va:
                
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
            mensaje_ticket = "¿Desea imprimir su ticket?"
            return render_template('terminar_venta.html', mensaje_ticket=mensaje_ticket)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al realizar la venta: {str(e)}', 'danger')
    return redirect(url_for('venta.ventas'))

@venta.route("/venta_pedido", methods=['GET','POST'])
def venta_pedido():
    pedidos=db.session.query(Venta).filter(Venta.estado == 'pendiente').join(usuario).all()
    return render_template('venta_pedido.html', pedidos=pedidos)

@venta.route("/realizar_venta_pedido/<int:id_venta>", methods=['GET','POST'])
def realizar_venta_pedido(id_venta):
    venta=db.session.query(Venta).filter_by(id_venta=id_venta).first()
    if request.method == 'POST':
        venta.estado = 'lista'
        venta.fecha_recogida = date.today()
        venta.pagado = 1
        try:
            db.session.commit()
            flash('Venta realizada con exito', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la venta', 'danger')

    return redirect(url_for('venta.venta_pedido'))