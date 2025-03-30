from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify
from flask import flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db
from models import Venta

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

        flash("Venta agregada correctamente.", "success")
        return redirect(url_for('venta.ventas'))

    flash("Error al procesar la venta.", "danger")
    return render_template('venta.html', form=form, ventas=session.get('ventas_acumuladas', []))

@venta.route("/terminar_venta", methods=['POST','GET'])
def terminar_venta():
    form = forms_ventas.VentaForm(request.form)
    session.pop('ventas_acumuladas', None)
    return redirect(url_for('venta.ventas'))

@venta.route("/eliminar_venta/<int:indice>", methods=['POST', 'GET'])
def eliminar_venta(indice):
    va = session['ventas_acumuladas']
    va.pop(indice)
    session['ventas_acumuladas'] = va
    
    return redirect(url_for('venta.ventas'))

@venta.route("/realizar_venta", methods=['POST', 'GET'])
def realizar_venta():

    

    return redirect(url_for('venta.ventas'))