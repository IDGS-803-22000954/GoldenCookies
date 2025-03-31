from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from models import db, Produccion, ProduccionInsumo, Merma, LoteGalleta, LoteInsumo, Receta, Galleta, Insumo
from produccion.forms import (ProduccionForm, MermaInsumoForm,
                              MermaGalletaForm, FinalizarProduccionForm, BuscarProduccionForm)
from collections import defaultdict
from datetime import datetime, timedelta

# Crear blueprint para rutas de producción
produccion_bp = Blueprint('produccion', __name__, url_prefix='/produccion')


# Listar producciones
@produccion_bp.route('/', methods=['GET', 'POST'])
def index():
    form = BuscarProduccionForm()

    # Iniciar consulta
    query = Produccion.query.join(Receta).join(Galleta)

    # Aplicar filtros si el formulario se envió
    if form.validate_on_submit():
        if form.estatus.data:
            query = query.filter(Produccion.estatus == form.estatus.data)
        if form.fecha_inicio.data:
            query = query.filter(Produccion.created_at >=
                                 form.fecha_inicio.data)
        if form.galleta.data:
            query = query.filter(Galleta.nombre.like(f'%{form.galleta.data}%'))

    # Ordenar por fecha de creación (más reciente primero)
    producciones = query.order_by(Produccion.created_at.desc()).all()

    return render_template('produccion.html', producciones=producciones, form=form)


# Nueva producción
@produccion_bp.route('/crear', methods=['GET', 'POST'])
def crear():
    form = ProduccionForm()

    if form.validate_on_submit():
        nueva_produccion = Produccion(
            estatus=form.estatus.data,
            id_usuario=current_user.id_usuario,  # Usamos el usuario actual
            id_receta=form.receta.data.id_receta
        )

        db.session.add(nueva_produccion)
        db.session.commit()

        flash(
            f'Producción #{nueva_produccion.id_produccion} creada correctamente', 'success')
        return redirect(url_for('produccion.detalle', id=nueva_produccion.id_produccion))

    return render_template('crear_produccion.html', form=form)


# Ver detalle de producción
@produccion_bp.route('/<int:id>', methods=['GET'])
def detalle(id):
    produccion = Produccion.query.get_or_404(id)
    insumos_usados = ProduccionInsumo.query.filter_by(id_produccion=id).all()
    mermas = Merma.query.filter_by(id_produccion=id).all()

    # Si la producción está completada, mostrar también el lote de galleta
    lote_galleta = None
    if produccion.estatus == 'completada' and produccion.id_lote_galleta:
        lote_galleta = LoteGalleta.query.get(produccion.id_lote_galleta)

    # Calcular costos basados en insumos usados
    costo_total = sum(pi.cantidad_usada *
                      pi.lote_insumo.costo_unitario for pi in insumos_usados)

    # Verificar la disponibilidad de insumos para la receta
    insumos_disponibles = True
    insumos_insuficientes = []

    if produccion.estatus == 'programada':
        # Verificar disponibilidad de insumos en la tabla Insumo (cantidad total)
        for ri in produccion.receta.receta_insumo:
            # Obtener la cantidad total disponible del insumo
            insumo = Insumo.query.get(ri.id_insumo)
            cantidad_disponible = insumo.cantidad_insumo

            if cantidad_disponible < ri.cantidad_insumo:
                insumos_disponibles = False
                insumos_insuficientes.append({
                    'nombre': ri.insumo.nombre,
                    'requerido': ri.cantidad_insumo,
                    'disponible': cantidad_disponible,
                    'unidad': ri.insumo.unidad_medida
                })

    return render_template('detalle_produccion.html',
                           produccion=produccion,
                           insumos_usados=insumos_usados,
                           mermas=mermas,
                           lote_galleta=lote_galleta,
                           costo_total=costo_total,
                           insumos_disponibles=insumos_disponibles,
                           insumos_insuficientes=insumos_insuficientes)


@produccion_bp.route('/iniciar/<int:id>', methods=['POST'])
def iniciar(id):
    produccion = Produccion.query.get_or_404(id)

    if produccion.estatus != 'programada':
        flash('Solo se pueden iniciar producciones programadas', 'warning')
        return redirect(url_for('produccion.detalle', id=id))

    # Verificar disponibilidad de insumos antes de iniciar usando la cantidad total en tabla Insumo
    insumos_insuficientes = []

    for ri in produccion.receta.receta_insumo:
        # Obtener la cantidad total disponible del insumo
        insumo = Insumo.query.get(ri.id_insumo)
        cantidad_disponible = insumo.cantidad_insumo

        if cantidad_disponible < ri.cantidad_insumo:
            insumos_insuficientes.append({
                'nombre': ri.insumo.nombre,
                'requerido': ri.cantidad_insumo,
                'disponible': cantidad_disponible,
                'unidad': ri.insumo.unidad_medida
            })

    if insumos_insuficientes:
        mensaje = "No se puede iniciar la producción por falta de insumos: "
        for insumo in insumos_insuficientes:
            mensaje += f"{insumo['nombre']}: se requiere {insumo['requerido']} {insumo['unidad']} pero solo hay {insumo['disponible']} disponible. "
        flash(mensaje, 'danger')
        return redirect(url_for('produccion.detalle', id=id))

    produccion.estatus = 'en_proceso'
    db.session.commit()

    flash('Producción iniciada correctamente', 'success')
    return redirect(url_for('produccion.detalle', id=id))


@produccion_bp.route('/mermas', methods=['GET'])
def listar_mermas():
    # Consultar todas las mermas ordenadas por fecha (más reciente primero)
    mermas = Merma.query.order_by(Merma.fecha_registro.desc()).all()

    # Calcular totales por tipo de merma
    mermas_por_tipo = db.session.query(
        Merma.tipo_merma, func.sum(Merma.cantidad).label('total')
    ).group_by(Merma.tipo_merma).all()

    # Calcular totales por material (galletas vs insumos)
    total_galletas = db.session.query(func.sum(Merma.cantidad)).filter(
        Merma.id_lote_galleta != None).scalar() or 0
    total_insumos = len(db.session.query(Merma.id_merma).filter(
        Merma.id_lote_insumo != None).all())

    return render_template('mermas.html',
                           mermas=mermas,
                           mermas_por_tipo=mermas_por_tipo,
                           total_galletas=total_galletas,
                           total_insumos=total_insumos)

# Modificación de la función finalizar (producción)


@produccion_bp.route('/finalizar/<int:id>', methods=['POST'])
def finalizar(id):
    produccion = Produccion.query.get_or_404(id)

    # Validar que la producción esté en proceso
    if produccion.estatus != 'en_proceso':
        flash('Solo se pueden finalizar producciones programadas o en proceso', 'warning')
        return redirect(url_for('produccion.detalle', id=id))

    # Obtener la receta y sus insumos
    receta = produccion.receta
    receta_insumos = receta.receta_insumo

    # Verificar disponibilidad de insumos y realizar el uso
    insumos_insuficientes = []
    costo_total = 0

    for ri in receta_insumos:
        # Verificar si hay suficientes insumos en la tabla Insumo
        insumo = Insumo.query.get(ri.id_insumo)
        if insumo.cantidad_insumo < ri.cantidad_insumo:
            insumos_insuficientes.append({
                'nombre': insumo.nombre,
                'requerido': ri.cantidad_insumo,
                'disponible': insumo.cantidad_insumo,
                'unidad': insumo.unidad_medida
            })
            continue

        # Calcular costo aproximado basado en el promedio o un valor predeterminado
        # Ya que no estamos usando lotes, necesitamos determinar el costo de alguna manera
        # Podríamos obtener el costo promedio de los lotes más recientes o usar un valor predeterminado
        costo_unitario_aprox = 0

        # Opción 1: Usar el promedio de los últimos lotes (si existen)
        lotes_recientes = LoteInsumo.query.filter_by(id_insumo=ri.id_insumo)\
            .order_by(LoteInsumo.fecha_compra.desc())\
            .limit(3).all()

        if lotes_recientes:
            costo_unitario_aprox = sum(
                lote.costo_unitario for lote in lotes_recientes) / len(lotes_recientes)
        else:
            # Opción 2: Usar el precio sugerido de la receta o un valor predeterminado
            costo_unitario_aprox = 1.0  # Valor predeterminado si no hay información

        # Calcular el costo de este insumo
        costo_insumo = ri.cantidad_insumo * costo_unitario_aprox
        costo_total += costo_insumo

        # Actualizar la cantidad total del insumo
        insumo.cantidad_insumo -= ri.cantidad_insumo

    # Si hay insumos insuficientes, no continuar
    if insumos_insuficientes:
        db.session.rollback()
        mensaje = "No hay suficientes insumos para completar la producción: "
        for insumo in insumos_insuficientes:
            mensaje += f"{insumo['nombre']}: se requiere {insumo['requerido']} {insumo['unidad']} pero solo hay {insumo['disponible']} disponible. "
        flash(mensaje, 'danger')
        return redirect(url_for('produccion.detalle', id=id))

    # Calcular costos
    cantidad_galletas = receta.cantidad_produccion
    costo_unitario = costo_total / cantidad_galletas if cantidad_galletas > 0 else 0

    # Crear lote de galletas automáticamente
    nuevo_lote = LoteGalleta(
        cantidad_inicial=cantidad_galletas,
        cantidad_disponible=cantidad_galletas,
        precio_venta=receta.galleta.precio_sugerido,
        costo_total_produccion=costo_total,
        costo_unitario=costo_unitario,
        fecha_produccion=datetime.now(),
        fecha_caducidad=datetime.now() + timedelta(days=21),
        id_galleta=receta.id_galleta,
        id_receta=receta.id_receta
    )

    db.session.add(nuevo_lote)
    db.session.flush()  # Para obtener el ID del lote

    # Actualizar producción
    produccion.estatus = 'completada'
    produccion.id_lote_galleta = nuevo_lote.id_lote_galleta

    # Actualizar inventario de galletas
    receta.galleta.cantidad_galletas += cantidad_galletas

    db.session.commit()

    flash('Producción finalizada correctamente. Se han utilizado los insumos y se ha creado el lote de galletas.', 'success')
    return redirect(url_for('produccion.detalle', id=id))


# Modificar la función de merma de insumo
@produccion_bp.route('/merma/insumo', methods=['GET', 'POST'])
def merma_insumo():
    form = MermaInsumoForm()

    if request.method == 'POST':
        print("Datos del formulario:", request.form)

        if form.validate_on_submit():
            print("Formulario validado correctamente")

            try:
                # Verificar cantidad disponible
                lote_insumo = form.lote_insumo.data
                print(
                    f"Lote insumo seleccionado: {lote_insumo.id_lote_insumo}, disponible: {lote_insumo.cantidad_disponible}")

                if lote_insumo.cantidad_disponible < form.cantidad.data:
                    flash(
                        f'La cantidad excede lo disponible. Máximo: {lote_insumo.cantidad_disponible} {lote_insumo.insumo.unidad_medida}', 'danger')
                    return redirect(url_for('produccion.merma_insumo'))

                # Registrar la merma
                nueva_merma = Merma(
                    tipo_merma=form.tipo_merma.data,
                    cantidad=form.cantidad.data,
                    fecha_registro=form.fecha_registro.data,
                    id_produccion=form.produccion.data.id_produccion if form.produccion.data else None,
                    id_lote_insumo=lote_insumo.id_lote_insumo,
                    motivo=form.motivo.data
                )
                print("Merma creada en memoria:", vars(nueva_merma))

                # Actualizar la cantidad disponible en el lote
                lote_insumo.cantidad_disponible -= form.cantidad.data

                # NUEVO: Actualizar la cantidad total en la tabla Insumo
                lote_insumo.insumo.cantidad_insumo -= form.cantidad.data

                db.session.add(nueva_merma)
                db.session.commit()
                print("Merma guardada en la base de datos con ID:",
                      nueva_merma.id_merma)

                flash('Merma de insumo registrada correctamente', 'success')
                return redirect(url_for('produccion.merma_insumo'))
            except Exception as e:
                db.session.rollback()
                print("ERROR AL REGISTRAR MERMA:", str(e))
                flash(f'Error al registrar merma: {str(e)}', 'danger')
        else:
            print("Errores de validación del formulario:", form.errors)

    return render_template('merma_insumo.html', form=form)


# Modificar la función de merma de galleta
@produccion_bp.route('/merma/galleta', methods=['GET', 'POST'])
def merma_galleta():
    form = MermaGalletaForm()

    if form.validate_on_submit():
        # Verificar cantidad disponible
        lote_galleta = form.lote_galleta.data
        if lote_galleta.cantidad_disponible < form.cantidad.data:
            flash(
                f'La cantidad excede lo disponible. Máximo: {lote_galleta.cantidad_disponible}', 'danger')
            return redirect(url_for('produccion.merma_galleta'))

        # Registrar la merma
        nueva_merma = Merma(
            tipo_merma=form.tipo_merma.data,
            cantidad=form.cantidad.data,
            fecha_registro=form.fecha_registro.data,
            id_produccion=form.produccion.data.id_produccion if form.produccion.data else None,
            id_lote_galleta=lote_galleta.id_lote_galleta,
            motivo=form.motivo.data
        )

        # Actualizar la cantidad disponible en el lote
        lote_galleta.cantidad_disponible -= form.cantidad.data

        # NUEVO: Actualizar la cantidad total en la tabla Galleta
        lote_galleta.galleta.cantidad_galletas -= form.cantidad.data

        db.session.add(nueva_merma)
        db.session.commit()

        flash('Merma de galleta registrada correctamente', 'success')
        return redirect(url_for('produccion.merma_galleta'))

    return render_template('merma_galleta.html', form=form)
# Cancelar producción


@produccion_bp.route('/cancelar/<int:id>', methods=['POST'])
def cancelar(id):
    produccion = Produccion.query.get_or_404(id)

    # Solo se pueden cancelar producciones que no estén completadas
    if produccion.estatus == 'completada':
        flash('No se puede cancelar una producción ya completada', 'danger')
        return redirect(url_for('produccion.detalle', id=id))

    produccion.estatus = 'cancelada'
    db.session.commit()

    flash('Producción cancelada correctamente', 'success')
    return redirect(url_for('produccion.detalle', id=id))


# Obtener costos unitarios vía AJAX
@produccion_bp.route('/calcular-costo', methods=['POST'])
def calcular_costo():
    id_produccion = request.json.get('id_produccion')
    cantidad = request.json.get('cantidad')

    if not id_produccion or not cantidad or cantidad <= 0:
        return jsonify({'error': 'Datos inválidos'}), 400

    # Calcular costos basados en insumos usados
    insumos_usados = ProduccionInsumo.query.filter_by(
        id_produccion=id_produccion).all()
    costo_total = sum(pi.cantidad_usada *
                      pi.lote_insumo.costo_unitario for pi in insumos_usados)
    costo_unitario = costo_total / cantidad

    return jsonify({
        'costo_total': costo_total,
        'costo_unitario': costo_unitario
    })


# Estadísticas de producción
@produccion_bp.route('/estadisticas', methods=['GET'])
def estadisticas():
    # Producciones por estatus
    estatus_count = db.session.query(
        Produccion.estatus, func.count(Produccion.id_produccion)
    ).group_by(Produccion.estatus).all()

    # Top 5 galletas más producidas
    top_galletas = db.session.query(
        Galleta.nombre, func.sum(LoteGalleta.cantidad_inicial).label('total')
    ).join(LoteGalleta).join(Produccion, Produccion.id_lote_galleta == LoteGalleta.id_lote_galleta)\
     .group_by(Galleta.id_galleta)\
     .order_by(func.sum(LoteGalleta.cantidad_inicial).desc())\
     .limit(5).all()

    # Top 5 insumos más utilizados
    top_insumos = db.session.query(
        Insumo.nombre, func.sum(ProduccionInsumo.cantidad_usada).label('total')
    ).join(LoteInsumo, ProduccionInsumo.id_lote_insumo == LoteInsumo.id_lote_insumo)\
     .join(Insumo, LoteInsumo.id_insumo == Insumo.id_insumo)\
     .group_by(Insumo.id_insumo)\
     .order_by(func.sum(ProduccionInsumo.cantidad_usada).desc())\
     .limit(5).all()

    # Mermas por tipo
    mermas = db.session.query(
        Merma.tipo_merma, func.sum(Merma.cantidad).label('total')
    ).group_by(Merma.tipo_merma).all()

    return render_template('estadisticas.html',
                           estatus_count=estatus_count,
                           top_galletas=top_galletas,
                           top_insumos=top_insumos,
                           mermas=mermas)
