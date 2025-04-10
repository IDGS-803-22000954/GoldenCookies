from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json
import calendar
from decimal import Decimal
from auth import verificar_roles

from models import db, Galleta, Venta, DetalleVenta, LoteGalleta, Insumo, LoteInsumo

# Crear el blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Clase personalizada de codificador JSON para manejar objetos Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Función de ayuda para formatear moneda


def format_money(amount):
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

# Función para formatear números


def number_format(num):
    if num is None:
        return "0"
    return f"{num:,}"


@dashboard_bp.route('/')
@login_required
@verificar_roles('admin', 'ventas', 'produccion')
def index():
    # Verificar que el usuario tenga permisos (admin, ventas o producción)
    if current_user.rol.lower() not in ['admin', 'ventas', 'produccion']:
        return render_template('error.html', message="No tienes permiso para acceder a esta página")

    # 1. Obtener datos generales para las estadísticas

    # Ventas totales (monto)
    total_sales = db.session.query(func.sum(Venta.total)).scalar() or 0
    # Convertir a float si es Decimal
    if isinstance(total_sales, Decimal):
        total_sales = float(total_sales)

    # Calcular tendencia de ventas (comparando con el mes pasado)
    today = datetime.now()
    first_of_month = datetime(today.year, today.month, 1)
    first_of_last_month = first_of_month - timedelta(days=1)
    first_of_last_month = datetime(
        first_of_last_month.year, first_of_last_month.month, 1)

    # Ventas de este mes
    current_month_sales = db.session.query(func.sum(Venta.total))\
        .filter(Venta.created_at >= first_of_month)\
        .scalar() or 0
    if isinstance(current_month_sales, Decimal):
        current_month_sales = float(current_month_sales)

    # Ventas del mes pasado
    last_month_sales = db.session.query(func.sum(Venta.total))\
        .filter(Venta.created_at >= first_of_last_month, Venta.created_at < first_of_month)\
        .scalar() or 0
    if isinstance(last_month_sales, Decimal):
        last_month_sales = float(last_month_sales)

    # Calcular tendencia (porcentaje de cambio)
    sales_trend = 0
    if last_month_sales > 0:
        sales_trend = round(
            ((current_month_sales - last_month_sales) / last_month_sales) * 100, 1)

    # 2. Galletas vendidas (cantidad)
    total_cookies_sold = db.session.query(
        func.sum(DetalleVenta.cantidad)).scalar() or 0
    if isinstance(total_cookies_sold, Decimal):
        total_cookies_sold = float(total_cookies_sold)

    # Tendencia de galletas vendidas
    current_month_cookies = db.session.query(func.sum(DetalleVenta.cantidad))\
        .join(Venta, Venta.id_venta == DetalleVenta.id_venta)\
        .filter(Venta.created_at >= first_of_month)\
        .scalar() or 0
    if isinstance(current_month_cookies, Decimal):
        current_month_cookies = float(current_month_cookies)

    last_month_cookies = db.session.query(func.sum(DetalleVenta.cantidad))\
        .join(Venta, Venta.id_venta == DetalleVenta.id_venta)\
        .filter(Venta.created_at >= first_of_last_month, Venta.created_at < first_of_month)\
        .scalar() or 0
    if isinstance(last_month_cookies, Decimal):
        last_month_cookies = float(last_month_cookies)

    cookies_trend = 0
    if last_month_cookies > 0:
        cookies_trend = round(
            ((current_month_cookies - last_month_cookies) / last_month_cookies) * 100, 1)

    # 3. Valor de inventario
    # Valor de inventario de galletas
    cookies_inventory_value = db.session.query(
        func.sum(Galleta.cantidad_galletas *
                 func.coalesce(
                     # Obtenemos costo promedio de producción para cada galleta
                     db.session.query(
                         func.avg(LoteGalleta.costo_unitario_produccion))
                     .filter(LoteGalleta.id_galleta == Galleta.id_galleta)
                     .scalar_subquery(),
                     0  # Valor por defecto si no hay lotes
                 ))
    ).scalar() or 0
    if isinstance(cookies_inventory_value, Decimal):
        cookies_inventory_value = float(cookies_inventory_value)

    # Valor de inventario de insumos
    ingredients_inventory_value = db.session.query(
        func.sum(LoteInsumo.cantidad_disponible *
                 (LoteInsumo.costo_total / LoteInsumo.cantidad))
    ).scalar() or 0
    if isinstance(ingredients_inventory_value, Decimal):
        ingredients_inventory_value = float(ingredients_inventory_value)

    # Valor total del inventario
    inventory_value = cookies_inventory_value + ingredients_inventory_value

    # Cambio en el valor del inventario (simplificado)
    inventory_growth = 5.2  # Este valor debería calcularse con datos históricos

    # 4. Ganancia esperada (basada en inventario de galletas)
    expected_revenue = db.session.query(
        func.sum(Galleta.cantidad_galletas * Galleta.precio)
    ).scalar() or 0
    if isinstance(expected_revenue, Decimal):
        expected_revenue = float(expected_revenue)

    expected_profit = expected_revenue - cookies_inventory_value
    profit_margin = 0
    if expected_revenue > 0:
        profit_margin = round((expected_profit / expected_revenue) * 100, 1)

    # 5. Datos para el gráfico de ventas por galleta
    cookie_sales_data = db.session.query(
        Galleta.nombre,
        func.sum(DetalleVenta.cantidad).label('total_sold')
    ).join(
        DetalleVenta, DetalleVenta.id_galleta == Galleta.id_galleta
    ).group_by(
        Galleta.nombre
    ).order_by(
        desc('total_sold')
    ).limit(6).all()

    cookie_names = [item[0] for item in cookie_sales_data]
    cookie_sales = [float(item[1]) if isinstance(
        item[1], Decimal) else item[1] for item in cookie_sales_data]

    # 6. Datos para el gráfico de tendencia de ventas
    # Obtener los últimos 6 meses de datos
    months_data = []
    sales_trend_data = []

    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1)
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1)

        # Ventas de ese mes
        month_sales = db.session.query(func.sum(Venta.total))\
            .filter(Venta.created_at >= month_start, Venta.created_at < month_end)\
            .scalar() or 0

        # Convertir a float si es Decimal
        if isinstance(month_sales, Decimal):
            month_sales = float(month_sales)

        month_name = calendar.month_name[month_date.month][:3]
        months_data.append(f"{month_name}")
        sales_trend_data.append(float(month_sales))

    # 7. Inventario de galletas
    cookies_inventory_query = db.session.query(
        Galleta.id_galleta,
        Galleta.nombre,
        Galleta.precio,
        Galleta.cantidad_galletas  # Usamos directamente el campo de la tabla Galleta
    ).all()

    # Convertir los resultados de la consulta en diccionarios para permitir añadir la ganancia estimada
    cookies_inventory = []
    for cookie in cookies_inventory_query:
        # Obtener costo promedio unitario de producción
        avg_cost = db.session.query(func.avg(LoteGalleta.costo_unitario_produccion))\
            .filter(LoteGalleta.id_galleta == cookie.id_galleta)\
            .scalar() or 0

        # Convert all values to float to ensure type consistency
        precio = float(cookie.precio) if cookie.precio is not None else 0
        avg_cost_float = float(avg_cost) if avg_cost is not None else 0
        # MODIFICACIÓN AQUÍ: Asegurar que cantidad_galletas nunca sea None
        cantidad = float(
            cookie.cantidad_galletas) if cookie.cantidad_galletas is not None else 0

        # Calculate estimated profit and add to a dictionary
        ganancia_estimada = (precio - avg_cost_float) * cantidad

        # Create a dictionary with all the cookie data plus the estimated profit
        # MODIFICACIÓN AQUÍ: Asegurar que cantidad_galletas nunca sea None en el diccionario
        cookie_dict = {
            'id_galleta': cookie.id_galleta,
            'nombre': cookie.nombre,
            'precio': float(cookie.precio) if isinstance(cookie.precio, Decimal) else cookie.precio,
            # Asegurar que nunca sea None
            'cantidad_galletas': float(cookie.cantidad_galletas) if isinstance(cookie.cantidad_galletas, Decimal) else (cookie.cantidad_galletas or 0),
            'ganancia_estimada': ganancia_estimada
        }

        cookies_inventory.append(cookie_dict)

    # 8. Recomendación de qué galleta vender
    # Criterios: mayor margen de ganancia y suficiente stock
    recommended_cookie = None
    max_potential_profit = 0

    for cookie in cookies_inventory:
        # MODIFICACIÓN AQUÍ: Asegurar que cantidad_galletas nunca sea None en esta comparación
        if (cookie.get('cantidad_galletas') or 0) < 20:  # Ignorar galletas con poco stock
            continue

        avg_cost = db.session.query(func.avg(LoteGalleta.costo_unitario_produccion))\
            .filter(LoteGalleta.id_galleta == cookie['id_galleta'])\
            .scalar() or 0

        # Convert to float for safe calculation
        precio = float(cookie['precio']) if cookie['precio'] is not None else 0
        avg_cost_float = float(avg_cost) if avg_cost is not None else 0
        # MODIFICACIÓN AQUÍ: Asegurar que cantidad_galletas nunca sea None
        cantidad = float(cookie['cantidad_galletas']
                         ) if cookie['cantidad_galletas'] is not None else 0

        margin_percent = 0
        if precio > 0:
            margin_percent = ((precio - avg_cost_float) / precio) * 100

        potential_profit = margin_percent * cantidad

        if potential_profit > max_potential_profit:
            max_potential_profit = potential_profit
            recommended_cookie = {
                'id': cookie['id_galleta'],
                'name': cookie['nombre'],
                'price': cookie['precio'],
                'margin': round(margin_percent, 1),
                'stock': cookie['cantidad_galletas'],
                'reason': f"Esta galleta tiene un excelente margen de ganancia ({round(margin_percent, 1)}%) y hay suficiente stock disponible."
            }

    # Si no hay una recomendación, proporcionar un valor predeterminado
    if not recommended_cookie:
        recommended_cookie = {
            'id': 0,
            'name': 'No hay recomendación',
            'price': 0,
            'margin': 0,
            'stock': 0,
            'reason': "No hay suficiente inventario para hacer una recomendación. Considera producir más galletas."
        }

    # Pasar todos los datos a la plantilla
    return render_template('dashboard.html',
                           total_sales_amount=total_sales,
                           sales_trend=sales_trend,
                           total_cookies_sold=total_cookies_sold,
                           cookies_trend=cookies_trend,
                           inventory_value=inventory_value,
                           inventory_growth=inventory_growth,
                           expected_profit=expected_profit,
                           profit_margin=profit_margin,
                           cookie_names=json.dumps(cookie_names),
                           cookie_sales=json.dumps(
                               cookie_sales, cls=DecimalEncoder),
                           months=json.dumps(months_data),
                           sales_trend_data=json.dumps(
                               sales_trend_data, cls=DecimalEncoder),
                           cookies_inventory=cookies_inventory,
                           recommended_cookie=recommended_cookie,
                           today_date=today.strftime("%d/%m/%Y"),
                           format_money=format_money,
                           number_format=number_format
                           )

# Registrar filtros personalizados para Jinja


def register_template_filters(app):
    @app.template_filter('format_money')
    def _format_money(amount):
        return format_money(amount)

    @app.template_filter('number_format')
    def _number_format(num):
        return number_format(num)

    @app.template_filter('abs')
    def _abs(num):
        return abs(num)
