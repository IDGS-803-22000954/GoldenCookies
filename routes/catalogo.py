from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Galleta, Venta, DetalleVenta, Produccion, Receta
from datetime import datetime, timedelta

catalogo_bp = Blueprint('catalogo', __name__)


@catalogo_bp.route('/')
def index():
    """Vista principal del catálogo de galletas"""
    galletas = Galleta.query.all()
    return render_template('catalogo.html', galletas=galletas)


@catalogo_bp.route('/detalle/<int:id_galleta>')
def detalle(id_galleta):
    """Detalle de una galleta específica"""
    galleta = Galleta.query.get_or_404(id_galleta)
    return render_template('detalle.html', galleta=galleta)


@catalogo_bp.route('/agregar-carrito/<int:id_galleta>', methods=['POST'])
@login_required
def agregar_carrito(id_galleta):
    """Agregar galleta al carrito (solo usuarios autenticados)"""
    galleta = Galleta.query.get_or_404(id_galleta)
    cantidad = int(request.form.get('cantidad', 1))

    if cantidad <= 0:
        flash('La cantidad debe ser mayor a cero', 'error')
        return redirect(url_for('catalogo.detalle', id_galleta=id_galleta))

    # Inicializar carrito si no existe
    if 'carrito' not in session:
        session['carrito'] = []

    # Buscar si ya existe en el carrito para incrementar
    carrito = session['carrito']
    producto_encontrado = False

    for item in carrito:
        if item.get('id_galleta') == id_galleta:
            nueva_cantidad = item['cantidad'] + cantidad
            # Ya no verificamos que no exceda el stock disponible
            item['cantidad'] = nueva_cantidad
            producto_encontrado = True
            flash(
                f'Se actualizó la cantidad de {galleta.nombre} en tu carrito', 'success')
            break

    # Si no estaba en el carrito, agregarlo
    if not producto_encontrado:
        carrito.append({
            'id_galleta': id_galleta,
            'nombre': galleta.nombre,
            'precio': galleta.precio,
            'cantidad': cantidad,
            'imagen': galleta.imagen
        })
        flash(f'Se agregó {galleta.nombre} a tu carrito', 'success')

    session['carrito'] = carrito
    return redirect(url_for('catalogo.index'))


@catalogo_bp.route('/carrito')
@login_required
def ver_carrito():
    """Ver contenido del carrito (solo usuarios autenticados)"""
    if 'carrito' not in session or not session['carrito']:
        flash('Tu carrito está vacío', 'info')
        return redirect(url_for('catalogo.index'))

    carrito = session['carrito']
    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    # Calcular tiempo de espera para cada producto
    tiempo_espera_maximo = 0
    now = datetime.now()  # Para el cálculo de la fecha estimada de entrega

    for item in carrito:
        galleta = Galleta.query.get(item['id_galleta'])
        tiempo_espera = 0

        # Si no hay suficiente stock, calcular tiempo de fabricación
        if galleta.cantidad_galletas < item['cantidad']:
            cantidad_faltante = item['cantidad'] - galleta.cantidad_galletas
            tiempo_espera = galleta.tiempo_estimado_fabricacion(
                cantidad_faltante)

        item['tiempo_espera'] = tiempo_espera
        tiempo_espera_maximo = max(tiempo_espera_maximo, tiempo_espera)

    return render_template('carrito.html',
                           carrito=carrito,
                           total=total,
                           tiempo_espera_maximo=tiempo_espera_maximo,
                           now=now,
                           timedelta=timedelta)


@catalogo_bp.route('/carrito/eliminar/<int:id_galleta>', methods=['POST'])
@login_required
def eliminar_del_carrito(id_galleta):
    """Eliminar un producto del carrito"""
    if 'carrito' in session:
        carrito = session['carrito']
        for i, item in enumerate(carrito):
            if item.get('id_galleta') == id_galleta:
                del carrito[i]
                session['carrito'] = carrito
                flash('Producto eliminado del carrito', 'success')
                break

    return redirect(url_for('catalogo.ver_carrito'))


@catalogo_bp.route('/finalizar-compra', methods=['POST'])
@login_required
def finalizar_compra():
    """Finalizar la compra y crear el pedido"""
    if 'carrito' not in session or not session['carrito']:
        flash('No hay productos en el carrito', 'error')
        return redirect(url_for('catalogo.index'))

    carrito = session['carrito']
    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    # Calcular el tiempo máximo de espera para la fecha de recogida
    tiempo_espera_maximo = 0
    for item in carrito:
        galleta = Galleta.query.get(item['id_galleta'])
        if galleta.cantidad_galletas < item['cantidad']:
            cantidad_faltante = item['cantidad'] - galleta.cantidad_galletas
            tiempo_espera = galleta.tiempo_estimado_fabricacion(
                cantidad_faltante)
            tiempo_espera_maximo = max(tiempo_espera_maximo, tiempo_espera)

    # Crear nueva venta/pedido
    nueva_venta = Venta(
        tipo_venta='en línea',
        total=total,
        id_usuario=current_user.id_usuario,
        estado='pendiente',
        # Fecha de recogida basada en el tiempo máximo de producción
        fecha_recogida=datetime.now() + timedelta(days=tiempo_espera_maximo),
        pagado=1  # Asumimos pago al momento por ahora
    )

    db.session.add(nueva_venta)
    db.session.flush()  # Para obtener el ID generado

    # Lista para almacenar las galletas que requieren producción
    galletas_a_producir = []

    # Crear los detalles de venta para cada producto en el carrito
    for item in carrito:
        detalle = DetalleVenta(
            cantidad=item['cantidad'],
            precio_unitario=item['precio'],
            tipo_venta='en línea',
            id_venta=nueva_venta.id_venta,
            id_galleta=item['id_galleta']
        )
        db.session.add(detalle)

        # Actualizar el stock de galletas y verificar si se necesita producción
        galleta = Galleta.query.get(item['id_galleta'])

        # Si no hay suficientes galletas, registramos para producción
        if galleta.cantidad_galletas < item['cantidad']:
            galletas_a_producir.append({
                'galleta': galleta,
                'cantidad_faltante': item['cantidad'] - galleta.cantidad_galletas
            })

        # Actualizamos el stock (puede quedar en negativo temporalmente)
        galleta.cantidad_galletas -= item['cantidad']

    # Generar producciones automáticas para las galletas que lo requieren
    producciones_creadas = []
    for item in galletas_a_producir:
        galleta = item['galleta']
        cantidad_faltante = item['cantidad_faltante']

        # Buscar la receta de la galleta
        receta = Receta.query.filter_by(id_galleta=galleta.id_galleta).first()

        if receta:
            # Calcular cuántas producciones necesitamos
            cantidad_por_produccion = receta.cantidad_produccion
            producciones_necesarias = (
                cantidad_faltante + cantidad_por_produccion - 1) // cantidad_por_produccion

            for _ in range(producciones_necesarias):
                nueva_produccion = Produccion(
                    estatus='programada',
                    # Podría ser un usuario específico de producción
                    id_usuario=current_user.id_usuario,
                    id_receta=receta.id_receta
                )
                db.session.add(nueva_produccion)
                db.session.flush()  # Para obtener el ID generado

                producciones_creadas.append({
                    'id': nueva_produccion.id_produccion,
                    'galleta': galleta.nombre
                })

    # Si se crearon producciones, cambiar el estado del pedido
    if producciones_creadas:
        nueva_venta.estado = 'en_produccion'
    else:
        nueva_venta.estado = 'listo_para_recoger'

    db.session.commit()

    # Limpiar el carrito
    session.pop('carrito', None)

    # Mensaje de éxito diferente si se crearon producciones
    if producciones_creadas:
        if tiempo_espera_maximo > 0:
            flash(
                f'¡Tu pedido ha sido realizado con éxito! Algunas galletas requieren producción y estarán listas para la fecha de recogida ({nueva_venta.fecha_recogida.strftime("%d/%m/%Y")}).', 'success')
        else:
            flash('¡Tu pedido ha sido realizado con éxito! Se han creado órdenes de producción automáticamente.', 'success')
    else:
        flash('¡Tu pedido ha sido realizado con éxito!', 'success')

    # Si es un cliente, redirigir a la página de pedidos
    if current_user.rol == 'cliente':
        return redirect(url_for('catalogo.mis_pedidos'))
    else:
        # Si es admin o ventas, redirigir a la página de pedidos (admin)
        return redirect(url_for('venta.venta_pedido'))


@catalogo_bp.route('/notificar-produccion/<int:id_venta>', methods=['POST'])
@login_required
def notificar_produccion(id_venta):
    """Notificar al equipo de producción sobre una venta que requiere producción"""
    venta = Venta.query.get_or_404(id_venta)

    if current_user.id_usuario != venta.id_usuario and current_user.rol not in ['admin', 'ventas']:
        flash('No tienes permiso para acceder a esta venta', 'error')
        return redirect(url_for('catalogo.index'))

    # Buscar las producciones relacionadas con esta venta
    # Esta es una implementación simplificada; en un sistema real,
    # necesitaríamos una tabla de relación entre ventas y producciones
    producciones = Produccion.query.filter_by(
        id_usuario=venta.id_usuario,
        estatus='programada',
        # Aproximación: producciones creadas al mismo tiempo que la venta
        created_at=venta.created_at
    ).all()

    # Enviar notificación (correo, mensaje interno, etc.)
    # En este ejemplo, simplemente marcamos la venta
    venta.estado = 'en_produccion'  # Necesitarías agregar este estado a la enumeración
    db.session.commit()

    flash(
        f'Se ha notificado al equipo de producción sobre el pedido #{venta.id_venta}', 'success')
    return redirect(url_for('venta.venta_pedido'))


@catalogo_bp.route('/mis-pedidos')
@login_required
def mis_pedidos():
    """Ver los pedidos del cliente autenticado"""
    if current_user.rol != 'cliente':
        # Los administradores y vendedores pueden acceder a todos los pedidos desde otra vista
        return redirect(url_for('venta.venta_pedido'))

    # Obtener todos los pedidos del usuario actual
    pedidos = Venta.query.filter_by(id_usuario=current_user.id_usuario).order_by(
        Venta.created_at.desc()).all()

    return render_template('mis_pedidos.html', pedidos=pedidos)
