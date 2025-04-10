from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, FloatField, IntegerField, HiddenField, DateTimeField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from models import usuario, Receta, LoteGalleta, LoteInsumo, Produccion, Insumo, Galleta
from datetime import datetime


def get_usuarios():
    return usuario.query.filter(usuario.rol.in_(['admin', 'produccion'])).all()


def get_recetas():
    return Receta.query.all()


def get_producciones():
    return Produccion.query.filter(Produccion.estatus != 'cancelada').all()


def get_insumos_disponibles():
    # Obtenemos insumos con existencia mayor a 0
    return Insumo.query.filter(Insumo.cantidad_insumo > 0).all()


def get_galletas_disponibles():
    # Obtenemos galletas con existencia mayor a 0
    return Galleta.query.filter(Galleta.cantidad_galletas > 0).all()


class ProduccionForm(FlaskForm):
    # Este formulario se mantiene igual
    receta = QuerySelectField('Receta',
                              query_factory=get_recetas,
                              get_label=lambda r: f"{r.galleta.nombre} - {r.cantidad_produccion} unidades",
                              validators=[DataRequired()])

    estatus = SelectField('Estatus',
                          choices=[
                              ('programada', 'Programada'),
                              ('en_proceso', 'En Proceso'),
                              ('completada', 'Completada'),
                              ('cancelada', 'Cancelada')
                          ],
                          default='programada',
                          validators=[DataRequired()])

    submit = SubmitField('Crear Producción')


class MermaInsumoForm(FlaskForm):
    tipo_merma = SelectField('Tipo de Merma',
                             choices=[
                                 ('caducidad', 'Caducidad'),
                                 ('daño', 'Daño'),
                                 ('contaminación', 'Contaminación'),
                                 ('error_proceso', 'Error en Proceso'),
                                 ('rotura', 'Rotura'),
                                 ('calidad', 'Control de Calidad'),
                                 ('otro', 'Otro')
                             ],
                             validators=[DataRequired()])

    # Cambiamos de lote_insumo a insumo directamente
    insumo = QuerySelectField('Insumo',
                              query_factory=get_insumos_disponibles,
                              get_label=lambda i: f"{i.nombre} ({i.cantidad_insumo} {i.unidad_medida})",
                              validators=[DataRequired()])

    # Agregamos un campo para seleccionar el lote después
    lote_insumo = SelectField('Lote (opcional)',
                              choices=[],
                              validators=[Optional()])

    cantidad = FloatField('Cantidad', validators=[
        DataRequired(), NumberRange(min=0.01)])

    produccion = QuerySelectField('Producción Relacionada',
                                  query_factory=get_producciones,
                                  get_label=lambda p: f"#{p.id_produccion} - {p.receta.galleta.nombre}",
                                  allow_blank=True,
                                  blank_text='(Ninguna)',
                                  validators=[Optional()])

    motivo = TextAreaField('Motivo', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Registrar Merma')


class MermaGalletaForm(FlaskForm):
    tipo_merma = SelectField('Tipo de Merma',
                             choices=[
                                 ('caducidad', 'Caducidad'),
                                 ('daño', 'Daño'),
                                 ('contaminación', 'Contaminación'),
                                 ('error_proceso', 'Error en Proceso'),
                                 ('rotura', 'Rotura'),
                                 ('calidad', 'Control de Calidad'),
                                 ('otro', 'Otro')
                             ],
                             validators=[DataRequired()])

    # Cambiamos de lote_galleta a galleta directamente
    galleta = QuerySelectField('Galleta',
                               query_factory=get_galletas_disponibles,
                               get_label=lambda g: f"{g.nombre} ({g.cantidad_galletas})",
                               validators=[DataRequired()])

    # Agregamos un campo para seleccionar el lote después
    lote_galleta = SelectField('Lote (opcional)',
                               choices=[],
                               validators=[Optional()])

    cantidad = IntegerField('Cantidad', validators=[
        DataRequired(), NumberRange(min=1)])

    produccion = QuerySelectField('Producción Relacionada',
                                  query_factory=get_producciones,
                                  get_label=lambda p: f"#{p.id_produccion} - {p.receta.galleta.nombre}",
                                  allow_blank=True,
                                  blank_text='(Ninguna)',
                                  validators=[Optional()])

    motivo = TextAreaField('Motivo', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Registrar Merma')


class FinalizarProduccionForm(FlaskForm):
    cantidad_producida = IntegerField('Cantidad Producida', validators=[
                                      DataRequired(), NumberRange(min=1)])
    precio_venta = FloatField('Precio de Venta Unitario', validators=[
                              DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Finalizar Producción')


class BuscarProduccionForm(FlaskForm):
    estatus = SelectField('Estatus',
                          choices=[
                              ('', 'Todos'),
                              ('programada', 'Programada'),
                              ('en_proceso', 'En Proceso'),
                              ('completada', 'Completada'),
                              ('cancelada', 'Cancelada')
                          ],
                          default='',
                          validators=[Optional()])

    fecha_inicio = DateField(
        'Fecha Desde', format='%Y-%m-%d', validators=[Optional()])
    galleta = StringField('Galleta', validators=[Optional()])
    submit = SubmitField('Filtrar')
