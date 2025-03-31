from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db, Galleta
from flask import session
from flask import g
from recetas.forms_galletas import GalletaForm

galletas_bp = Blueprint('galletas', __name__, url_prefix='/galletas')

@galletas_bp.route("/", methods=['GET', 'POST'])
def galleta():
    galletas = Galleta.query.all()
    form = GalletaForm()
    return render_template('galletas.html', galletas=galletas, form=form)

@galletas_bp.route('/agregar', methods=['GET', 'POST'])
def agregar_galleta():
    form = GalletaForm()
    galletas = Galleta.query.all()  
    if form.validate_on_submit():
        nueva_galleta = Galleta(
            nombre=form.nombre.data,
            precio_sugerido=form.precio_sugerido.data,
            peso_unidad=form.peso_unidad.data,
            descripcion=form.descripcion.data
        )
        db.session.add(nueva_galleta)
        db.session.commit()
        flash('Galleta agregada con éxito', 'success')
        return redirect(url_for('galletas.galleta'))  
    return render_template('galletas.html', form=form, galletas=galletas)

@galletas_bp.route('/modificar/<int:id_galleta>', methods=['GET', 'POST'])
def modificar_galleta(id_galleta):
    galleta = Galleta.query.get_or_404(id_galleta)
    form = GalletaForm(obj=galleta)  
    galletas = Galleta.query.all()

    if form.validate_on_submit():
        galleta.nombre = form.nombre.data
        galleta.precio_sugerido = form.precio_sugerido.data
        galleta.peso_unidad = form.peso_unidad.data
        galleta.descripcion = form.descripcion.data
        db.session.commit()
        flash('Galleta modificada con éxito', 'info')
        return redirect(url_for('galletas.galleta'))

    return render_template('galletas.html', form=form, galletas=galletas)


