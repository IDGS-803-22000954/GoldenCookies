from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response, jsonify, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import forms_ventas
from models import db, Venta, DetalleVenta, usuario, Galleta
from datetime import date, datetime
from auth import verificar_roles
from sqlalchemy import or_

venta = Blueprint('venta', __name__)


def redondear_precio_mxn(precio):
    """
    Redondea un precio al estilo mexicano:
    - Si el precio tiene decimales menores o iguales a 50 centavos, redondea a 50 centavos
    - Si el precio tiene decimales mayores a 50 centavos, redondea al entero superior

    Args:
        precio (float): El precio original

    Returns:
        float: El precio redondeado
    """
    entero = int(precio)
    decimal = precio - entero

    if decimal == 0:
        # Ya es un número entero, lo dejamos así
        return precio
    elif decimal <= 0.5:
        # Redondeamos a 50 centavos
        return entero + 0.5
    else:
        # Redondeamos al entero superior
        return entero + 1.0


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
        galleta = db.session.query(Galleta).filter_by(
            id_galleta=form.galleta.data).first()

        # Calcular cantidad real de galletas según el tipo de venta
        tipo_venta = form.tipo_venta.data
        cantidad_solicitada = form.cantidad.data

        if tipo_venta == "unidad":
            galletas_reales = cantidad_solicitada
        elif tipo_venta == "paquete_10":
            galletas_reales = cantidad_solicitada * 10
        elif tipo_venta == "paquete_20":
            galletas_reales = cantidad_solicitada * 20
        elif tipo_venta == "paquete_30":
            galletas_reales = cantidad_solicitada * 30
        elif tipo_venta == "docena":
            galletas_reales = cantidad_solicitada * 12

        cantidad_disponible = galleta.cantidad_galletas

        if galletas_reales > cantidad_disponible:
            flash(
                f"No hay suficientes galletas disponibles para '{galleta.nombre}'. Solicitadas: {galletas_reales}, Disponibles: {cantidad_disponible}", 'danger')
        else:
            if 'ventas_acumuladas' not in session:
                session['ventas_acumuladas'] = []
            ventas = session['ventas_acumuladas']

            # Calcular precio con posibles descuentos según tipo de paquete
            if tipo_venta == "unidad":
                precio_total = cantidad_solicitada * galleta.precio
            elif tipo_venta == "paquete_10":
                precio_total = cantidad_solicitada * 10 * galleta.precio * 0.95  # 5% descuento
            elif tipo_venta == "paquete_20":
                precio_total = cantidad_solicitada * 20 * \
                    galleta.precio * 0.90  # 10% descuento
            elif tipo_venta == "paquete_30":
                precio_total = cantidad_solicitada * 30 * \
                    galleta.precio * 0.85  # 15% descuento
            elif tipo_venta == "docena":
                precio_total = cantidad_solicitada * 12 * galleta.precio * 0.95  # 5% descuento

            # Aplicar redondeo al precio total para el estilo mexicano
            precio_total = redondear_precio_mxn(precio_total)

            nueva_venta = {
                "id_galleta": galleta.id_galleta,
                "galleta": galleta.nombre,
                "tipo_venta": tipo_venta,
                "cantidad": cantidad_solicitada,
                "precio": precio_total,
                "galletas_reales": galletas_reales  # Guardar la cantidad real para usarla después
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
@verificar_roles('admin', 'ventas')
@login_required
def eliminar_venta(indice):
    va = session.get('ventas_acumuladas', [])
    # Funciona tanto con GET como con POST
    if indice < len(va):
        producto_eliminado = va.pop(indice)
        flash(
            f"Se eliminó {producto_eliminado['galleta']} del carrito", 'info')
    else:
        flash("No se pudo eliminar el producto", 'danger')

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

            # No redondeamos el total de nuevo ya que cada producto ya fue redondeado

            nueva_venta = Venta(
                tipo_venta='local',
                total=ptotal,
                id_usuario=session.get('id_usuario'),
                created_at=datetime.now(),
                fecha_recogida=date.today(),
                pagado=1
            )
            db.session.add(nueva_venta)
            db.session.flush()

            idv = nueva_venta.id_venta

            for v in va:
                galleta = db.session.query(Galleta).filter_by(
                    id_galleta=v["id_galleta"]).first()

                if galleta:
                    # Usar la cantidad real de galletas (ya calculada en procesar_tabla)
                    galletas_reales = v["galletas_reales"]

                    if galleta.cantidad_galletas >= galletas_reales:
                        galleta.cantidad_galletas -= galletas_reales
                    else:
                        flash(
                            f"No hay suficientes galletas disponibles para '{galleta.nombre}'", 'warning')
                        db.session.rollback()
                        return redirect(url_for('venta.ventas'))

                # Almacenar el detalle de venta
                nuevo_detalle = DetalleVenta(
                    cantidad=int(v["cantidad"]),
                    precio_unitario=float(v["precio"]),  # Precio ya redondeado
                    tipo_venta=v["tipo_venta"],
                    id_galleta=int(v['id_galleta']),
                    id_venta=idv,
                    created_at=datetime.now()
                )
                db.session.add(nuevo_detalle)

            db.session.commit()
            flash('Venta realizada con éxito', 'success')
            session.pop('ventas_acumuladas', None)
            return redirect(url_for('venta.ventas'))

        except Exception as e:
            db.session.rollback()
            flash(f'{str(e)}', 'danger')
            flash(f'Error al realizar la venta', 'danger')
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

        detalles = db.session.query(
            DetalleVenta).filter_by(id_venta=id_venta).all()
        try:
            for detalle in detalles:
                # Find the corresponding Galleta
                galleta = db.session.query(Galleta).filter_by(
                    id_galleta=detalle.id_galleta).first()

                if galleta:
                    # Calcular cantidad real de galletas según el tipo de venta
                    tipo_venta = detalle.tipo_venta
                    cantidad_solicitada = detalle.cantidad

                    if tipo_venta == "unidad":
                        galletas_reales = cantidad_solicitada
                    elif tipo_venta == "paquete_10":
                        galletas_reales = cantidad_solicitada * 10
                    elif tipo_venta == "paquete_20":
                        galletas_reales = cantidad_solicitada * 20
                    elif tipo_venta == "paquete_30":
                        galletas_reales = cantidad_solicitada * 30
                    elif tipo_venta == "docena":
                        galletas_reales = cantidad_solicitada * 12
                    else:
                        galletas_reales = cantidad_solicitada  # Caso por defecto

                    # Deduct the cantidad from galleta stock
                    if galleta.cantidad_galletas >= galletas_reales:
                        galleta.cantidad_galletas -= galletas_reales
                    else:
                        flash(
                            f"No hay suficientes galletas disponibles para '{galleta.nombre}'. Necesarias: {galletas_reales}", 'warning')
                        db.session.rollback()
                        return redirect(url_for('venta.venta_pedido'))
                else:
                    flash(
                        f"La galleta referenciada en el detalle de venta no existe.", 'danger')
                    db.session.rollback()
                    return redirect(url_for('venta.venta_pedido'))

            # Commit the transaction
            db.session.commit()
            flash('Pedido procesado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pedido: {str(e)}', 'danger')

    return redirect(url_for('venta.venta_pedido'))


@venta.route("/ganancias", methods=['GET', 'POST'])
@verificar_roles('admin', 'ventas')
@login_required
def ganancias():
    # Obtener fecha seleccionada o usar la fecha actual
    fecha_str = request.args.get('fecha')

    try:
        if fecha_str:
            try:
                fecha_seleccionada = datetime.strptime(
                    fecha_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha incorrecto', 'danger')
                fecha_seleccionada = date.today()
        else:
            fecha_seleccionada = date.today()

        # Buscar todas las ventas de la fecha con estado 'lista' y pagadas
        ventas = db.session.query(Venta).filter(
            Venta.fecha_recogida == fecha_seleccionada,
            Venta.pagado == 1,
            # Algunas ventas pueden no tener estado
            or_(Venta.estado == 'lista', Venta.estado == None)
        ).join(usuario).all()

        total_ventas = len(ventas)
        total_cantidad = sum(venta.total for venta in ventas) if ventas else 0

        # Aplicar redondeo al total para el reporte
        total_cantidad = redondear_precio_mxn(total_cantidad)

        # Si no hay ventas, mostrar un mensaje pero no redirigir
        if not ventas and fecha_str:
            flash(
                f'No hay ventas registradas para la fecha {fecha_seleccionada.strftime("%d/%m/%Y")}', 'info')

        return render_template(
            'ganancias.html',
            ventas=ventas,
            total_ventas=total_ventas,
            total_cantidad=total_cantidad,
            fecha_seleccionada=fecha_seleccionada
        )

    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error en ganancias: {str(e)}")
        print(traceback_str)
        flash(f'Error al cargar reporte: {str(e)}', 'danger')
        # En lugar de redirigir, renderizamos la plantilla con datos vacíos
        return render_template(
            'ganancias.html',
            ventas=[],
            total_ventas=0,
            total_cantidad=0,
            fecha_seleccionada=date.today()
        )
