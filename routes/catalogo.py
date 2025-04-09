from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Galleta, Venta, DetalleVenta
from datetime import datetime

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

    if cantidad > galleta.cantidad_galletas:
        flash(
            f'Solo hay {galleta.cantidad_galletas} galletas disponibles', 'error')
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
            # Verificar que no exceda el stock disponible
            if nueva_cantidad <= galleta.cantidad_galletas:
                item['cantidad'] = nueva_cantidad
                producto_encontrado = True
                flash(
                    f'Se actualizó la cantidad de {galleta.nombre} en tu carrito', 'success')
            else:
                flash(
                    f'No se puede agregar más de {galleta.cantidad_galletas} unidades', 'error')
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

    return render_template('carrito.html', carrito=carrito, total=total)


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

    # Crear nueva venta/pedido
    nueva_venta = Venta(
        tipo_venta='en línea',
        total=total,
        id_usuario=current_user.id_usuario,
        estado='pendiente',
        # Se podría permitir al usuario seleccionar esta fecha
        fecha_recogida=datetime.now(),
        pagado=1  # Asumimos pago al momento por ahora
    )

    db.session.add(nueva_venta)
    db.session.flush()  # Para obtener el ID generado

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

        # Actualizar el stock de galletas
        galleta = Galleta.query.get(item['id_galleta'])
        galleta.cantidad_galletas -= item['cantidad']

    db.session.commit()

    # Limpiar el carrito
    session.pop('carrito', None)

    flash('¡Tu pedido ha sido realizado con éxito!', 'success')
    # Redirigir a la página de pedidos del cliente
    return redirect(url_for('venta.venta_pedido'))
