from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, Float, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, DateTime, text
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.orm import relationship
import datetime

db = SQLAlchemy()


class Galleta(db.Model):
    __tablename__ = 'galleta'

    id_galleta: int = db.Column(Integer, primary_key=True)
    nombre: str = db.Column(String(100))
    precio_sugerido: float = db.Column(Float)
    peso_unidad: float = db.Column(Float)
    descripcion: Optional[str] = db.Column(String(255))
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    receta: List['Receta'] = relationship('Receta', back_populates='galleta')
    lote_galleta: List['LoteGalleta'] = relationship(
        'LoteGalleta', back_populates='galleta')


class Insumo(db.Model):
    __tablename__ = 'insumo'

    id_insumo: int = db.Column(Integer, primary_key=True)
    nombre: str = db.Column(String(100))
    unidad_medida: str = db.Column(String(60))
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: List['LoteInsumo'] = relationship(
        'LoteInsumo', back_populates='insumo')
    receta_insumo: List['RecetaInsumo'] = relationship(
        'RecetaInsumo', back_populates='insumo')


class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    id_proveedor: int = db.Column(Integer, primary_key=True)
    nombre: str = db.Column(String(100))
    contacto: Optional[str] = db.Column(String(100))
    telefono: Optional[str] = db.Column(String(15))
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    compra_insumo: List['CompraInsumo'] = relationship(
        'CompraInsumo', back_populates='proveedor')


class Usuario(db.Model):
    __tablename__ = 'usuario'
    __table_args__ = (
        Index('nombre_usuario', 'nombre_usuario', unique=True),
    )

    id_usuario: int = db.Column(Integer, primary_key=True)
    nombre: str = db.Column(String(100))
    nombre_usuario: str = db.Column(String(50))
    contrasenia: str = db.Column(String(255))
    rol: str = db.Column(Enum('admin', 'ventas', 'produccion',
                         'cliente'), server_default=text("'cliente'"))
    telefono: str = db.Column(String(15))
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    ultimo_login: Optional[datetime.datetime] = db.Column(DateTime)
    intentos_fallidos: Optional[int] = db.Column(
        Integer, server_default=text("'0'"))
    bloqueado: Optional[int] = db.Column(
        TINYINT(1), server_default=text("'0'"))
    codigo_2fa: Optional[str] = db.Column(String(8))

    log: List['Log'] = relationship('Log', back_populates='usuario')
    venta: List['Venta'] = relationship('Venta', back_populates='usuario')
    produccion: List['Produccion'] = relationship(
        'Produccion', back_populates='usuario')


class Log(db.Model):
    __tablename__ = 'log'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_usuario'], ['usuario.id_usuario'], name='log_ibfk_1'),
        Index('id_usuario', 'id_usuario')
    )

    id_log: int = db.Column(Integer, primary_key=True)
    tipo_evento: str = db.Column(String(50))
    fecha_evento: datetime.datetime = db.Column(DateTime)
    id_usuario: Optional[int] = db.Column(Integer)

    usuario: Optional['Usuario'] = relationship(
        'Usuario', back_populates='log')


class LoteInsumo(db.Model):
    __tablename__ = 'lote_insumo'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_insumo'], ['insumo.id_insumo'], name='lote_insumo_ibfk_1'),
        Index('id_insumo', 'id_insumo')
    )

    id_lote_insumo: int = db.Column(Integer, primary_key=True)
    cantidad: float = db.Column(Float)
    cantidad_disponible: float = db.Column(Float)
    costo_unitario: float = db.Column(Float)
    fecha_compra: datetime.datetime = db.Column(DateTime)
    fecha_caducidad: datetime.datetime = db.Column(DateTime)
    id_insumo: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    insumo: Optional['Insumo'] = relationship(
        'Insumo', back_populates='lote_insumo')
    compra_insumo: List['CompraInsumo'] = relationship(
        'CompraInsumo', back_populates='lote_insumo')
    merma: List['Merma'] = relationship('Merma', back_populates='lote_insumo')
    produccion_insumo: List['ProduccionInsumo'] = relationship(
        'ProduccionInsumo', back_populates='lote_insumo')


class Receta(db.Model):
    __tablename__ = 'receta'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_galleta'], ['galleta.id_galleta'], name='receta_ibfk_1'),
        Index('id_galleta', 'id_galleta')
    )

    id_receta: int = db.Column(Integer, primary_key=True)
    cantidad_produccion: int = db.Column(Integer)
    id_galleta: Optional[int] = db.Column(Integer)
    descripcion: Optional[str] = db.Column(LONGTEXT)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    galleta: Optional['Galleta'] = relationship(
        'Galleta', back_populates='receta')
    lote_galleta: List['LoteGalleta'] = relationship(
        'LoteGalleta', back_populates='receta')
    receta_insumo: List['RecetaInsumo'] = relationship(
        'RecetaInsumo', back_populates='receta')
    produccion: List['Produccion'] = relationship(
        'Produccion', back_populates='receta')


class Venta(db.Model):
    __tablename__ = 'venta'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_usuario'], ['usuario.id_usuario'], name='venta_ibfk_1'),
        Index('id_usuario', 'id_usuario')
    )

    id_venta: int = db.Column(Integer, primary_key=True)
    fecha: datetime.datetime = db.Column(DateTime)
    tipo_venta: str = db.Column(String(50))
    total: float = db.Column(Float)
    metodo_pago: str = db.Column(String(50))
    id_usuario: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    estado: Optional[str] = db.Column(
        Enum('pendiente', 'lista'), server_default=text("'lista'"))
    fecha_recogida: Optional[datetime.datetime] = db.Column(DateTime)
    pagado: Optional[int] = db.Column(TINYINT(1), server_default=text("'1'"))

    usuario: Optional['Usuario'] = relationship(
        'Usuario', back_populates='venta')
    detalle_venta: List['DetalleVenta'] = relationship(
        'DetalleVenta', back_populates='venta')


class CompraInsumo(db.Model):
    __tablename__ = 'compra_insumo'
    __table_args__ = (
        ForeignKeyConstraint(['id_lote_insumo'], [
                             'lote_insumo.id_lote_insumo'], name='compra_insumo_ibfk_2'),
        ForeignKeyConstraint(['id_proveedor'], [
                             'proveedor.id_proveedor'], name='compra_insumo_ibfk_1'),
        Index('id_lote_insumo', 'id_lote_insumo'),
        Index('id_proveedor', 'id_proveedor')
    )

    id_compra: int = db.Column(Integer, primary_key=True)
    presentacion: str = db.Column(String(50))
    cantidad_normalizada: float = db.Column(Float)
    precio_total: float = db.Column(Float)
    id_proveedor: Optional[int] = db.Column(Integer)
    id_lote_insumo: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: Optional['LoteInsumo'] = relationship(
        'LoteInsumo', back_populates='compra_insumo')
    proveedor: Optional['Proveedor'] = relationship(
        'Proveedor', back_populates='compra_insumo')


class LoteGalleta(db.Model):
    __tablename__ = 'lote_galleta'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_galleta'], ['galleta.id_galleta'], name='lote_galleta_ibfk_1'),
        ForeignKeyConstraint(
            ['id_receta'], ['receta.id_receta'], name='lote_galleta_ibfk_2'),
        Index('id_galleta', 'id_galleta'),
        Index('id_receta', 'id_receta')
    )

    id_lote_galleta: int = db.Column(Integer, primary_key=True)
    cantidad_inicial: int = db.Column(Integer)
    cantidad_disponible: int = db.Column(Integer)
    precio_venta: float = db.Column(Float)
    costo_total_produccion: float = db.Column(Float)
    costo_unitario: float = db.Column(Float)
    fecha_produccion: datetime.datetime = db.Column(DateTime)
    fecha_caducidad: datetime.datetime = db.Column(DateTime)
    id_galleta: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    id_receta: Optional[int] = db.Column(Integer)

    galleta: Optional['Galleta'] = relationship(
        'Galleta', back_populates='lote_galleta')
    receta: Optional['Receta'] = relationship(
        'Receta', back_populates='lote_galleta')
    detalle_venta: List['DetalleVenta'] = relationship(
        'DetalleVenta', back_populates='lote_galleta')
    produccion: List['Produccion'] = relationship(
        'Produccion', back_populates='lote_galleta')
    merma: List['Merma'] = relationship('Merma', back_populates='lote_galleta')


class RecetaInsumo(db.Model):
    __tablename__ = 'receta_insumo'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_insumo'], ['insumo.id_insumo'], name='receta_insumo_ibfk_2'),
        ForeignKeyConstraint(
            ['id_receta'], ['receta.id_receta'], name='receta_insumo_ibfk_1'),
        Index('id_insumo', 'id_insumo'),
        Index('id_receta', 'id_receta')
    )

    id_receta_insumo: int = db.Column(Integer, primary_key=True)
    cantidad_insumo: float = db.Column(Float)
    id_receta: Optional[int] = db.Column(Integer)
    id_insumo: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    insumo: Optional['Insumo'] = relationship(
        'Insumo', back_populates='receta_insumo')
    receta: Optional['Receta'] = relationship(
        'Receta', back_populates='receta_insumo')


class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    __table_args__ = (
        ForeignKeyConstraint(['id_lote_galleta'], [
                             'lote_galleta.id_lote_galleta'], name='detalle_venta_ibfk_2'),
        ForeignKeyConstraint(['id_venta'], ['venta.id_venta'],
                             name='detalle_venta_ibfk_1'),
        Index('id_lote_galleta', 'id_lote_galleta'),
        Index('id_venta', 'id_venta')
    )

    id_detalle: int = db.Column(Integer, primary_key=True)
    cantidad: int = db.Column(Integer)
    precio_unitario: float = db.Column(Float)
    tipo_venta: str = db.Column(
        Enum('pieza', 'gramos', '700g', '1kg'), server_default=text("'pieza'"))
    id_venta: Optional[int] = db.Column(Integer)
    id_lote_galleta: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Optional['LoteGalleta'] = relationship(
        'LoteGalleta', back_populates='detalle_venta')
    venta: Optional['Venta'] = relationship(
        'Venta', back_populates='detalle_venta')


class Produccion(db.Model):
    __tablename__ = 'produccion'
    __table_args__ = (
        ForeignKeyConstraint(['id_lote_galleta'], [
                             'lote_galleta.id_lote_galleta'], name='produccion_ibfk_2'),
        ForeignKeyConstraint(
            ['id_receta'], ['receta.id_receta'], name='produccion_ibfk_3'),
        ForeignKeyConstraint(
            ['id_usuario'], ['usuario.id_usuario'], name='produccion_ibfk_1'),
        Index('id_lote_galleta', 'id_lote_galleta'),
        Index('id_receta', 'id_receta'),
        Index('id_usuario', 'id_usuario')
    )

    id_produccion: int = db.Column(Integer, primary_key=True)
    estatus: str = db.Column(String(100))
    id_usuario: Optional[int] = db.Column(Integer)
    id_lote_galleta: Optional[int] = db.Column(Integer)
    id_receta: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Optional['LoteGalleta'] = relationship(
        'LoteGalleta', back_populates='produccion')
    receta: Optional['Receta'] = relationship(
        'Receta', back_populates='produccion')
    usuario: Optional['Usuario'] = relationship(
        'Usuario', back_populates='produccion')
    merma: List['Merma'] = relationship('Merma', back_populates='produccion')
    produccion_insumo: List['ProduccionInsumo'] = relationship(
        'ProduccionInsumo', back_populates='produccion')


class Merma(db.Model):
    __tablename__ = 'merma'
    __table_args__ = (
        ForeignKeyConstraint(['id_lote_galleta'], [
                             'lote_galleta.id_lote_galleta'], name='merma_ibfk_3'),
        ForeignKeyConstraint(['id_lote_insumo'], [
                             'lote_insumo.id_lote_insumo'], name='merma_ibfk_2'),
        ForeignKeyConstraint(['id_produccion'], [
                             'produccion.id_produccion'], name='merma_ibfk_1'),
        Index('id_lote_galleta', 'id_lote_galleta'),
        Index('id_lote_insumo', 'id_lote_insumo'),
        Index('id_produccion', 'id_produccion')
    )

    id_merma: int = db.Column(Integer, primary_key=True)
    tipo_merma: str = db.Column(String(50))
    cantidad: float = db.Column(Float)
    fecha_registro: datetime.datetime = db.Column(DateTime)
    id_produccion: Optional[int] = db.Column(Integer)
    id_lote_insumo: Optional[int] = db.Column(Integer)
    id_lote_galleta: Optional[int] = db.Column(Integer)
    motivo: Optional[str] = db.Column(String(255))
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Optional['LoteGalleta'] = relationship(
        'LoteGalleta', back_populates='merma')
    lote_insumo: Optional['LoteInsumo'] = relationship(
        'LoteInsumo', back_populates='merma')
    produccion: Optional['Produccion'] = relationship(
        'Produccion', back_populates='merma')


class ProduccionInsumo(db.Model):
    __tablename__ = 'produccion_insumo'
    __table_args__ = (
        ForeignKeyConstraint(['id_lote_insumo'], [
                             'lote_insumo.id_lote_insumo'], name='produccion_insumo_ibfk_2'),
        ForeignKeyConstraint(['id_produccion'], [
                             'produccion.id_produccion'], name='produccion_insumo_ibfk_1'),
        Index('id_lote_insumo', 'id_lote_insumo'),
        Index('id_produccion', 'id_produccion')
    )

    id_produccion_insumo: int = db.Column(Integer, primary_key=True)
    cantidad_usada: float = db.Column(Float)
    id_produccion: Optional[int] = db.Column(Integer)
    id_lote_insumo: Optional[int] = db.Column(Integer)
    created_at: Optional[datetime.datetime] = db.Column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: Optional['LoteInsumo'] = relationship(
        'LoteInsumo', back_populates='produccion_insumo')
    produccion: Optional['Produccion'] = relationship(
        'Produccion', back_populates='produccion_insumo')
