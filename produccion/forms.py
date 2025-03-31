from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, FloatField, IntegerField, HiddenField, DateTimeField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField
from models import usuario, Receta, LoteGalleta, LoteInsumo, Produccion
from datetime import datetime


def get_usuarios():
    return usuario.query.filter(usuario.rol.in_(['admin', 'produccion'])).all()


def get_recetas():
    return Receta.query.all()


def get_lotes_galleta():
    return LoteGalleta.query.filter(LoteGalleta.cantidad_disponible > 0).all()


def get_producciones():
    return Produccion.query.filter(Produccion.estatus != 'cancelada').all()


class ProduccionForm(FlaskForm):
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

    lote_insumo = QuerySelectField('Lote de Insumo',
                                   query_factory=lambda: LoteInsumo.query.filter(
                                       LoteInsumo.cantidad_disponible > 0).all(),
                                   get_label=lambda li: f"{li.insumo.nombre} - Lote #{li.id_lote_insumo} ({li.cantidad_disponible} {li.insumo.unidad_medida} disponibles)",
                                   validators=[DataRequired()])

    cantidad = FloatField('Cantidad', validators=[
                          DataRequired(), NumberRange(min=0.01)])

    fecha_registro = DateTimeField('Fecha de Registro',
                                   default=datetime.now,
                                   format='%Y-%m-%dT%H:%M',  # Cambiar a este formato
                                   validators=[DataRequired()])

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

    lote_galleta = QuerySelectField('Lote de Galleta',
                                    query_factory=get_lotes_galleta,
                                    get_label=lambda lg: f"{lg.galleta.nombre} - Lote #{lg.id_lote_galleta} ({lg.cantidad_disponible} unidades)",
                                    validators=[DataRequired()])

    cantidad = IntegerField('Cantidad', validators=[
                            DataRequired(), NumberRange(min=1)])

    fecha_registro = DateTimeField('Fecha de Registro',
                                   default=datetime.now,
                                   format='%Y-%m-%dT%H:%M',  # Cambiar a este formato
                                   validators=[DataRequired()])

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
