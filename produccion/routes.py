from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from models import db, Produccion, ProduccionInsumo, Merma, LoteGalleta, LoteInsumo, Receta, Galleta, Insumo, Venta, DetalleVenta
from produccion.forms import (ProduccionForm, MermaInsumoForm,
                              MermaGalletaForm, FinalizarProduccionForm, BuscarProduccionForm)
from collections import defaultdict
from datetime import datetime, timedelta
from auth import verificar_roles

produccion_bp = Blueprint('produccion', __name__, url_prefix='/produccion')


@produccion_bp.route('/', methods=['GET', 'POST'])
@verificar_roles('admin', 'produccion')
@login_required
def index():
    form = BuscarProduccionForm()

    query = Produccion.query.join(Receta).join(Galleta)

    if form.validate_on_submit():
        if form.estatus.data:
            query = query.filter(Produccion.estatus == form.estatus.data)
        if form.fecha_inicio.data:
            query = query.filter(Produccion.created_at >=
                                 form.fecha_inicio.data)
        if form.galleta.data:
            query = query.filter(Galleta.nombre.like(f'%{form.galleta.data}%'))

    producciones = query.order_by(Produccion.created_at.desc()).all()

    return render_template('produccion.html', producciones=producciones, form=form)


@produccion_bp.route('/crear', methods=['GET', 'POST'])
@verificar_roles('admin', 'produccion')
@login_required
def crear():
    form = ProduccionForm()

    if form.validate_on_submit():
        nueva_produccion = Produccion(
            estatus=form.estatus.data,
            id_usuario=current_user.id_usuario,
            id_receta=form.receta.data.id_receta
        )

        db.session.add(nueva_produccion)
        db.session.commit()

        flash(
            f'Producción #{nueva_produccion.id_produccion} creada correctamente', 'success')
        return redirect(url_for('produccion.detalle', id=nueva_produccion.id_produccion))

    return render_template('crear_produccion.html', form=form)


@produccion_bp.route('/<int:id>', methods=['GET'])
@verificar_roles('admin', 'produccion')
@login_required
def detalle(id):
    produccion = Produccion.query.get_or_404(id)
    insumos_usados = ProduccionInsumo.query.filter_by(id_produccion=id).all()
    mermas = Merma.query.filter_by(id_produccion=id).all()

    lote_galleta = None
    if produccion.estatus == 'completada' and produccion.id_lote_galleta:
        lote_galleta = LoteGalleta.query.get(produccion.id_lote_galleta)

    # Crear un diccionario para obtener fácilmente los insumos usados por id_insumo
    insumos_usados_dict = {}
    costo_total = 0

    for pi in insumos_usados:
        lote_insumo = pi.lote_insumo
        if lote_insumo:
            insumo = lote_insumo.insumo
            if insumo:
                insumos_usados_dict[insumo.id_insumo] = {
                    'cantidad_usada': pi.cantidad_usada,
                    'costo_unitario': lote_insumo.costo_total / lote_insumo.cantidad if lote_insumo.cantidad > 0 else 0,
                    'lote_insumo': lote_insumo
                }
                costo_total += pi.cantidad_usada * \
                    (lote_insumo.costo_total /
                     lote_insumo.cantidad if lote_insumo.cantidad > 0 else 0)

    insumos_disponibles = True
    insumos_insuficientes = []

    if produccion.estatus == 'programada':
        for ri in produccion.receta.receta_insumo:
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
                           insumos_usados_dict=insumos_usados_dict,
                           mermas=mermas,
                           lote_galleta=lote_galleta,
                           costo_total=costo_total,
                           insumos_disponibles=insumos_disponibles,
                           insumos_insuficientes=insumos_insuficientes)


@produccion_bp.route('/iniciar/<int:id>', methods=['POST'])
@verificar_roles('admin', 'produccion')
@login_required
def iniciar(id):
    produccion = Produccion.query.get_or_404(id)

    if produccion.estatus != 'programada':
        flash('Solo se pueden iniciar producciones programadas', 'warning')
        return redirect(url_for('produccion.detalle', id=id))

    insumos_insuficientes = []

    for ri in produccion.receta.receta_insumo:
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
@verificar_roles('admin', 'produccion')
@login_required
def listar_mermas():
    mermas = Merma.query.order_by(Merma.created_at.desc()).all()

    mermas_por_tipo = db.session.query(
        Merma.tipo_merma, func.sum(Merma.cantidad).label('total')
    ).group_by(Merma.tipo_merma).all()

    total_galletas = db.session.query(func.sum(Merma.cantidad)).filter(
        Merma.id_lote_galleta != None).scalar() or 0
    total_insumos = len(db.session.query(Merma.id_merma).filter(
        Merma.id_lote_insumo != None).all())

    total_galletas_registros = len(db.session.query(Merma.cantidad).filter(
        Merma.id_lote_insumo != None).all())

    return render_template('mermas.html',
                           mermas=mermas,
                           mermas_por_tipo=mermas_por_tipo,
                           total_galletas=total_galletas,
                           total_insumos=total_insumos,
                           total_galletas_registros=total_galletas_registros)


@produccion_bp.route('/finalizar/<int:id>', methods=['POST'])
@verificar_roles('admin', 'produccion')
@login_required
def finalizar(id):
    produccion = Produccion.query.get_or_404(id)

    if produccion.estatus != 'en_proceso':
        flash('Solo se pueden finalizar producciones programadas o en proceso', 'warning')
        return redirect(url_for('produccion.detalle', id=id))

    receta = produccion.receta
    receta_insumos = receta.receta_insumo

    insumos_insuficientes = []
    costo_total = 0

    for ri in receta_insumos:
        insumo = Insumo.query.get(ri.id_insumo)
        if insumo.cantidad_insumo < ri.cantidad_insumo:
            insumos_insuficientes.append({
                'nombre': insumo.nombre,
                'requerido': ri.cantidad_insumo,
                'disponible': insumo.cantidad_insumo,
                'unidad': insumo.unidad_medida
            })
            continue

        costo_unitario_aprox = 0

        lotes_recientes = LoteInsumo.query.filter_by(id_insumo=ri.id_insumo)\
            .order_by(LoteInsumo.created_at.desc())\
            .limit(3).all()

        if lotes_recientes:
            costo_unitario_aprox = sum(
                lote.costo_total/lote.cantidad for lote in lotes_recientes) / len(lotes_recientes)
        else:
            costo_unitario_aprox = 1.0

        costo_insumo = ri.cantidad_insumo * costo_unitario_aprox
        costo_total += costo_insumo

        insumo.cantidad_insumo -= ri.cantidad_insumo

    if insumos_insuficientes:
        db.session.rollback()
        mensaje = "No hay suficientes insumos para completar la producción: "
        for insumo in insumos_insuficientes:
            mensaje += f"{insumo['nombre']}: se requiere {insumo['requerido']} {insumo['unidad']} pero solo hay {insumo['disponible']} disponible. "
        flash(mensaje, 'danger')
        return redirect(url_for('produccion.detalle', id=id))

    cantidad_galletas = receta.cantidad_produccion
    costo_unitario = costo_total / cantidad_galletas if cantidad_galletas > 0 else 0

    nuevo_lote = LoteGalleta(
        cantidad_inicial=cantidad_galletas,
        cantidad_disponible=cantidad_galletas,
        precio_venta=receta.galleta.precio,
        costo_total_produccion=costo_total,
        costo_unitario_produccion=costo_unitario,
        created_at=datetime.now(),
        fecha_caducidad=datetime.now() + timedelta(days=21),
        id_galleta=receta.id_galleta,
        id_receta=receta.id_receta
    )

    db.session.add(nuevo_lote)
    db.session.flush()

    produccion.estatus = 'completada'
    produccion.id_lote_galleta = nuevo_lote.id_lote_galleta

    receta.galleta.cantidad_galletas += cantidad_galletas

    db.session.commit()

    # NUEVO: Actualizar pedidos relacionados con esta producción
    actualizar_pedidos_post_produccion(produccion)

    flash('Producción finalizada correctamente. Se han utilizado los insumos y se ha creado el lote de galletas.', 'success')
    return redirect(url_for('produccion.detalle', id=id))


def actualizar_pedidos_post_produccion(produccion):
    """
    Actualiza los pedidos relacionados después de finalizar una producción.
    Busca pedidos en estado 'en_produccion' y verifica si la galleta producida
    satisface alguno de los pedidos pendientes.
    """
    # Obtener la galleta producida
    galleta_producida = None
    if produccion.receta and produccion.receta.galleta:
        galleta_producida = produccion.receta.galleta

    if not galleta_producida:
        return  # No podemos actualizar pedidos si no hay galleta identificable

    # Buscar todos los pedidos en producción
    pedidos_potenciales = Venta.query.filter(
        Venta.estado == 'en_produccion'
    ).all()

    for pedido in pedidos_potenciales:
        # Verificar si todas las galletas del pedido están disponibles
        detalles = DetalleVenta.query.filter_by(id_venta=pedido.id_venta).all()
        todas_disponibles = True

        for detalle in detalles:
            galleta = Galleta.query.get(detalle.id_galleta)
            if not galleta:
                continue

            # Calcular cantidad real según tipo de venta
            if detalle.tipo_venta == "unidad":
                galletas_reales = detalle.cantidad
            elif detalle.tipo_venta == "paquete_10":
                galletas_reales = detalle.cantidad * 10
            elif detalle.tipo_venta == "paquete_20":
                galletas_reales = detalle.cantidad * 20
            elif detalle.tipo_venta == "paquete_30":
                galletas_reales = detalle.cantidad * 30
            elif detalle.tipo_venta == "docena":
                galletas_reales = detalle.cantidad * 12
            else:
                galletas_reales = detalle.cantidad

            # Si no hay suficientes galletas disponibles, este pedido aún no está listo
            if galleta.cantidad_galletas < galletas_reales:
                todas_disponibles = False
                break

        # Si todas las galletas están disponibles, marcar como listo para recoger
        if todas_disponibles:
            pedido.estado = 'listo_para_recoger'
            db.session.commit()
            print(
                f"Pedido #{pedido.id_venta} actualizado a listo_para_recoger")

            # NUEVO: Notificar al cliente que su pedido está listo
            # Aquí podrías agregar lógica para enviar un correo electrónico o notificación


@produccion_bp.route('/merma/insumo', methods=['GET', 'POST'])
@verificar_roles('admin', 'produccion')
@login_required
def merma_insumo():
    form = MermaInsumoForm()

    if request.method == 'POST':
        print("Datos del formulario:", request.form)

        if form.validate_on_submit():
            print("Formulario validado correctamente")

            try:
                insumo = form.insumo.data
                lote_id = form.lote_insumo.data if form.lote_insumo.data else None

                print(f"Insumo seleccionado: {insumo.nombre}")
                print(f"Cantidad disponible total: {insumo.cantidad_insumo}")

                # Validar contra la cantidad total del insumo
                if insumo.cantidad_insumo < form.cantidad.data:
                    flash(
                        f'La cantidad excede lo disponible en inventario. Máximo: {insumo.cantidad_insumo} {insumo.unidad_medida}', 'danger')
                    return redirect(url_for('produccion.merma_insumo'))

                # Si se seleccionó un lote específico, usarlo
                if lote_id:
                    lote_insumo = LoteInsumo.query.get(lote_id)
                    if not lote_insumo or lote_insumo.id_insumo != insumo.id_insumo:
                        flash('El lote seleccionado no es válido', 'danger')
                        return redirect(url_for('produccion.merma_insumo'))
                else:
                    # Seleccionar automáticamente el lote más antiguo con disponibilidad
                    lote_insumo = LoteInsumo.query.filter(
                        LoteInsumo.id_insumo == insumo.id_insumo,
                        LoteInsumo.cantidad_disponible > 0
                    ).order_by(LoteInsumo.created_at).first()

                    if not lote_insumo:
                        flash(
                            'No se encontró ningún lote disponible para este insumo', 'danger')
                        return redirect(url_for('produccion.merma_insumo'))

                nueva_merma = Merma(
                    tipo_merma=form.tipo_merma.data,
                    cantidad=form.cantidad.data,
                    id_produccion=form.produccion.data.id_produccion if form.produccion.data else None,
                    id_lote_insumo=lote_insumo.id_lote_insumo,
                    motivo=form.motivo.data
                )
                print("Merma creada en memoria:", vars(nueva_merma))

                # Determinar cuánto podemos descontar del lote seleccionado
                cantidad_descontar_lote = min(
                    form.cantidad.data, lote_insumo.cantidad_disponible)
                lote_insumo.cantidad_disponible -= cantidad_descontar_lote

                # Actualizar el total del insumo
                insumo.cantidad_insumo -= form.cantidad.data

                # Si queda cantidad por descontar y hay más lotes, distribuir entre ellos
                cantidad_restante = form.cantidad.data - cantidad_descontar_lote
                if cantidad_restante > 0:
                    lotes_adicionales = LoteInsumo.query.filter(
                        LoteInsumo.id_insumo == insumo.id_insumo,
                        LoteInsumo.cantidad_disponible > 0,
                        LoteInsumo.id_lote_insumo != lote_insumo.id_lote_insumo
                    ).order_by(LoteInsumo.created_at).all()

                    for lote in lotes_adicionales:
                        if cantidad_restante <= 0:
                            break

                        descontar_de_este_lote = min(
                            cantidad_restante, lote.cantidad_disponible)
                        lote.cantidad_disponible -= descontar_de_este_lote
                        cantidad_restante -= descontar_de_este_lote

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


@produccion_bp.route('/merma/galleta', methods=['GET', 'POST'])
@verificar_roles('admin', 'produccion')
@login_required
def merma_galleta():
    form = MermaGalletaForm()

    if form.validate_on_submit():
        galleta = form.galleta.data
        lote_id = form.lote_galleta.data if form.lote_galleta.data else None

        # Validar contra la cantidad total de la galleta
        if galleta.cantidad_galletas < form.cantidad.data:
            flash(
                f'La cantidad excede lo disponible en inventario. Máximo: {galleta.cantidad_galletas} unidades', 'danger')
            return redirect(url_for('produccion.merma_galleta'))

        # Si se seleccionó un lote específico, usarlo
        if lote_id:
            lote_galleta = LoteGalleta.query.get(lote_id)
            if not lote_galleta or lote_galleta.id_galleta != galleta.id_galleta:
                flash('El lote seleccionado no es válido', 'danger')
                return redirect(url_for('produccion.merma_galleta'))
        else:
            # Seleccionar automáticamente el lote más antiguo con disponibilidad
            lote_galleta = LoteGalleta.query.filter(
                LoteGalleta.id_galleta == galleta.id_galleta,
                LoteGalleta.cantidad_disponible > 0
            ).order_by(LoteGalleta.created_at).first()

            if not lote_galleta:
                flash(
                    'No se encontró ningún lote disponible para esta galleta', 'danger')
                return redirect(url_for('produccion.merma_galleta'))

        nueva_merma = Merma(
            tipo_merma=form.tipo_merma.data,
            cantidad=form.cantidad.data,
            id_produccion=form.produccion.data.id_produccion if form.produccion.data else None,
            id_lote_galleta=lote_galleta.id_lote_galleta,
            motivo=form.motivo.data
        )

        # Determinar cuánto podemos descontar del lote seleccionado
        cantidad_descontar_lote = min(
            form.cantidad.data, lote_galleta.cantidad_disponible)
        lote_galleta.cantidad_disponible -= cantidad_descontar_lote

        # Actualizar el total de la galleta
        galleta.cantidad_galletas -= form.cantidad.data

        # Si queda cantidad por descontar y hay más lotes, distribuir entre ellos
        cantidad_restante = form.cantidad.data - cantidad_descontar_lote
        if cantidad_restante > 0:
            lotes_adicionales = LoteGalleta.query.filter(
                LoteGalleta.id_galleta == galleta.id_galleta,
                LoteGalleta.cantidad_disponible > 0,
                LoteGalleta.id_lote_galleta != lote_galleta.id_lote_galleta
            ).order_by(LoteGalleta.created_at).first()

            for lote in lotes_adicionales:
                if cantidad_restante <= 0:
                    break

                descontar_de_este_lote = min(
                    cantidad_restante, lote.cantidad_disponible)
                lote.cantidad_disponible -= descontar_de_este_lote
                cantidad_restante -= descontar_de_este_lote

        db.session.add(nueva_merma)
        db.session.commit()

        flash('Merma de galleta registrada correctamente', 'success')
        return redirect(url_for('produccion.merma_galleta'))

    return render_template('merma_galleta.html', form=form)


# Ruta para cargar lotes según el insumo seleccionado (para AJAX)
@produccion_bp.route('/lotes-insumo/<int:id_insumo>', methods=['GET'])
@verificar_roles('admin', 'produccion')
@login_required
def get_lotes_insumo(id_insumo):
    lotes = LoteInsumo.query.filter(
        LoteInsumo.id_insumo == id_insumo,
        LoteInsumo.cantidad_disponible > 0
    ).order_by(LoteInsumo.created_at).all()

    lotes_data = [{"id": lote.id_lote_insumo,
                   "label": f"Lote #{lote.id_lote_insumo} ({lote.cantidad_disponible} {lote.insumo.unidad_medida})"}
                  for lote in lotes]

    return jsonify(lotes_data)


# Ruta para cargar lotes según la galleta seleccionada (para AJAX)
@produccion_bp.route('/lotes-galleta/<int:id_galleta>', methods=['GET'])
@verificar_roles('admin', 'produccion')
@login_required
def get_lotes_galleta(id_galleta):
    lotes = LoteGalleta.query.filter(
        LoteGalleta.id_galleta == id_galleta,
        LoteGalleta.cantidad_disponible > 0
    ).order_by(LoteGalleta.created_at).all()

    lotes_data = [{"id": lote.id_lote_galleta,
                   "label": f"Lote #{lote.id_lote_galleta} ({lote.cantidad_disponible})"}
                  for lote in lotes]

    return jsonify(lotes_data)


@produccion_bp.route('/cancelar/<int:id>', methods=['POST'])
@verificar_roles('admin', 'produccion')
@login_required
def cancelar(id):
    produccion = Produccion.query.get_or_404(id)

    if produccion.estatus == 'completada':
        flash('No se puede cancelar una producción ya completada', 'danger')
        return redirect(url_for('produccion.detalle', id=id))

    produccion.estatus = 'cancelada'
    db.session.commit()

    flash('Producción cancelada correctamente', 'success')
    return redirect(url_for('produccion.detalle', id=id))


@produccion_bp.route('/calcular-costo', methods=['POST'])
def calcular_costo():
    id_produccion = request.json.get('id_produccion')
    cantidad = request.json.get('cantidad')

    if not id_produccion or not cantidad or cantidad <= 0:
        return jsonify({'error': 'Datos inválidos'}), 400

    insumos_usados = ProduccionInsumo.query.filter_by(
        id_produccion=id_produccion).all()
    costo_total = sum(pi.cantidad_usada *
                      pi.lote_insumo.costo_unitario for pi in insumos_usados)
    costo_unitario = costo_total / cantidad

    return jsonify({
        'costo_total': costo_total,
        'costo_unitario': costo_unitario
    })


@produccion_bp.route('/estadisticas', methods=['GET'])
@verificar_roles('admin', 'produccion')
@login_required
def estadisticas():
    # Consulta original - NO la modificamos
    estatus_count_raw = db.session.query(
        Produccion.estatus, func.count(Produccion.id_produccion)
    ).group_by(Produccion.estatus).all()

    # Convertimos a formato más manejable y calculamos total
    estatus_count = []
    total_producciones = 0
    completadas = 0
    en_proceso = 0
    programadas = 0
    canceladas = 0

    # Procesamos cada estatus
    for estatus, count in estatus_count_raw:
        # Sumar al total
        total_producciones += count

        # Guardar valores específicos
        if estatus == 'completada':
            completadas = count
        elif estatus == 'en_proceso':
            en_proceso = count
        elif estatus == 'programada':
            programadas = count
        elif estatus == 'cancelada':
            canceladas = count

        # Agregar a la lista procesada
        estatus_count.append((estatus, count))

    # Calculamos porcentajes
    estatus_porcentajes = []
    for estatus, count in estatus_count:
        if total_producciones > 0:
            porcentaje = round((count / total_producciones) * 100, 1)
        else:
            porcentaje = 0
        estatus_porcentajes.append((estatus, count, porcentaje))

    # El resto de consultas no las modificamos
    top_galletas = db.session.query(
        Galleta.nombre, func.sum(LoteGalleta.cantidad_inicial).label('total')
    ).join(LoteGalleta).join(Produccion, Produccion.id_lote_galleta == LoteGalleta.id_lote_galleta)\
     .group_by(Galleta.id_galleta)\
     .order_by(func.sum(LoteGalleta.cantidad_inicial).desc())\
     .limit(5).all()

    top_insumos = db.session.query(
        Insumo.nombre, func.sum(ProduccionInsumo.cantidad_usada).label('total')
    ).join(LoteInsumo, ProduccionInsumo.id_lote_insumo == LoteInsumo.id_lote_insumo)\
     .join(Insumo, LoteInsumo.id_insumo == Insumo.id_insumo)\
     .group_by(Insumo.id_insumo)\
     .order_by(func.sum(ProduccionInsumo.cantidad_usada).desc())\
     .limit(5).all()

    mermas = db.session.query(
        Merma.tipo_merma, func.sum(Merma.cantidad).label('total')
    ).group_by(Merma.tipo_merma).all()

    # Imprimimos para debug
    print("DATOS PROCESADOS:")
    print(f"Total producciones: {total_producciones}")
    print(f"Completadas: {completadas}")
    print(f"En proceso: {en_proceso}")
    print(f"Programadas: {programadas}")
    print(f"Canceladas: {canceladas}")
    print(f"Estatus con porcentajes: {estatus_porcentajes}")

    return render_template('estadisticas.html',
                           estatus_count=estatus_count,
                           estatus_porcentajes=estatus_porcentajes,
                           top_galletas=top_galletas,
                           top_insumos=top_insumos,
                           mermas=mermas,
                           total_producciones=total_producciones,
                           completadas=completadas,
                           en_proceso=en_proceso,
                           programadas=programadas,
                           canceladas=canceladas)
