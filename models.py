from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, Float, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, DateTime, text
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

db = SQLAlchemy()

class Log(db.Model):
    __tablename__ = 'log'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_usuario'], ['usuario.id_usuario'], name='log_ibfk_1'),
        Index('id_usuario', 'id_usuario')
    )

    id_log: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_evento: Mapped[str] = mapped_column(String(50))
    fecha_evento: Mapped[datetime.datetime] = mapped_column(DateTime)
    id_usuario: Mapped[Optional[int]] = mapped_column(Integer)

    usuario: Mapped[Optional['usuario']] = relationship(
        'usuario', back_populates='log')


class Galleta(db.Model):
    __tablename__ = 'galleta'

    id_galleta: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    cantidad_galletas: Mapped[int] = mapped_column(Integer)
    precio_sugerido: Mapped[float] = mapped_column(Float)
    peso_unidad: Mapped[float] = mapped_column(Float)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    receta: Mapped[List['Receta']] = relationship('Receta', back_populates='galleta')
    lote_galleta: Mapped[List['LoteGalleta']] = relationship(
        'LoteGalleta', back_populates='galleta')


class Insumo(db.Model):
    __tablename__ = 'insumo'

    id_insumo: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    unidad_medida: Mapped[str] = mapped_column(String(60))
    cantidad_insumo: Mapped[float]= mapped_column(Float)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: Mapped[List['LoteInsumo']] = relationship(
        'LoteInsumo', back_populates='insumo')
    receta_insumo: Mapped[List['RecetaInsumo']] = relationship(
        'RecetaInsumo', back_populates='insumo')


class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    id_proveedor: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    contacto: Mapped[Optional[str]] = mapped_column(String(100))
    telefono: Mapped[Optional[str]] = mapped_column(String(15))
    estatus = db.Column(db.Boolean, default=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    compra_insumo: Mapped[List['CompraInsumo']] = relationship(
        'CompraInsumo', back_populates='proveedor')


class usuario(db.Model, UserMixin):
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    nombre_usuario = db.Column(db.String(50), nullable=False, unique=True)
    contrasenia = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    rol = db.Column(db.Enum('admin', 'ventas', 'produccion', 'cliente', name='rol_enum'), nullable=False, default='cliente')
    telefono = db.Column(db.String(15), nullable=False)
    ultimo_login = db.Column(db.DateTime, nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado = db.Column(db.Boolean, default=False)
    codigo_2fa = db.Column(db.String(8), nullable=True)
    log: Mapped[List['Log']] = relationship('Log', back_populates='usuario')
    venta: Mapped[List['Venta']] = relationship('Venta', back_populates='usuario')
    produccion: Mapped[List['Produccion']] = relationship('Produccion', back_populates='usuario')
    email = db.Column(db.String(50), nullable=True)

    @classmethod
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_active(self):
        return not self.bloqueado  # Considera activo si no está bloqueado

    def is_authenticated(self):
        return True  # Siempre autenticado si ha iniciado sesión

    def is_anonymous(self):
        return False  # Nunca anónimo si ha iniciado sesión

    def get_id(self):
        return str(self.id_usuario) 


class LoteInsumo(db.Model):
    __tablename__ = 'lote_insumo'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_insumo'], ['insumo.id_insumo'], name='lote_insumo_ibfk_1'),
        Index('id_insumo', 'id_insumo')
    )

    id_lote_insumo: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad: Mapped[float] = mapped_column(Float)
    cantidad_disponible: Mapped[float] = mapped_column(Float)
    costo_unitario: Mapped[float] = mapped_column(Float)
    fecha_compra: Mapped[datetime.datetime] = mapped_column(DateTime)
    fecha_caducidad: Mapped[datetime.datetime] = mapped_column(DateTime)
    id_insumo: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    insumo: Mapped[Optional['Insumo']] = relationship(
        'Insumo', back_populates='lote_insumo')
    compra_insumo: Mapped[List['CompraInsumo']] = relationship(
        'CompraInsumo', back_populates='lote_insumo')
    merma: Mapped[List['Merma']] = relationship('Merma', back_populates='lote_insumo')
    produccion_insumo: Mapped[List['ProduccionInsumo']] = relationship(
        'ProduccionInsumo', back_populates='lote_insumo')


class Receta(db.Model):
    __tablename__ = 'receta'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_galleta'], ['galleta.id_galleta'], name='receta_ibfk_1'),
        Index('id_galleta', 'id_galleta')
    )

    id_receta: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad_produccion: Mapped[int] = mapped_column(Integer)
    id_galleta: Mapped[Optional[int]] = mapped_column(Integer)
    descripcion: Mapped[Optional[str]] = mapped_column(LONGTEXT)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    galleta: Mapped[Optional['Galleta']] = relationship(
        'Galleta', back_populates='receta')
    lote_galleta: Mapped[List['LoteGalleta']] = relationship(
        'LoteGalleta', back_populates='receta')
    receta_insumo: Mapped[List['RecetaInsumo']] = relationship(
        'RecetaInsumo', back_populates='receta')
    produccion: Mapped[List['Produccion']] = relationship(
        'Produccion', back_populates='receta')


class Venta(db.Model):
    __tablename__ = 'venta'
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_usuario'], ['usuario.id_usuario'], name='venta_ibfk_1'),
        Index('id_usuario', 'id_usuario')
    )

    id_venta: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime)
    tipo_venta: Mapped[str] = mapped_column(String(50))
    total: Mapped[float] = mapped_column(Float)
    metodo_pago: Mapped[str] = mapped_column(String(50))
    id_usuario: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    estado: Mapped[Optional[str]] = mapped_column(
        Enum('pendiente', 'lista'), server_default=text("'lista'"))
    fecha_recogida: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    pagado: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"))

    usuario: Mapped[Optional['usuario']] = relationship(
        'usuario', back_populates='venta')
    detalle_venta: Mapped[List['DetalleVenta']] = relationship(
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

    id_compra: Mapped[int] = mapped_column(Integer, primary_key=True)
    presentacion: Mapped[str] = mapped_column(String(50))
    cantidad_normalizada: Mapped[float] = mapped_column(Float)
    precio_total: Mapped[float] = mapped_column(Float)
    id_proveedor: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_insumo: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: Mapped[Optional['LoteInsumo']] = relationship(
        'LoteInsumo', back_populates='compra_insumo')
    proveedor: Mapped[Optional['Proveedor']] = relationship(
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

    id_lote_galleta: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad_inicial: Mapped[int] = mapped_column(Integer)
    cantidad_disponible: Mapped[int] = mapped_column(Integer)
    precio_venta: Mapped[float] = mapped_column(Float)
    costo_total_produccion: Mapped[float] = mapped_column(Float)
    costo_unitario: Mapped[float] = mapped_column(Float)
    fecha_produccion: Mapped[datetime.datetime] = mapped_column(DateTime)
    fecha_caducidad: Mapped[datetime.datetime] = mapped_column(DateTime)
    id_galleta: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    id_receta: Mapped[Optional[int]] = mapped_column(Integer)

    galleta: Mapped[Optional['Galleta']] = relationship(
        'Galleta', back_populates='lote_galleta')
    receta: Mapped[Optional['Receta']] = relationship(
        'Receta', back_populates='lote_galleta')
    detalle_venta: Mapped[List['DetalleVenta']] = relationship(
        'DetalleVenta', back_populates='lote_galleta')
    produccion: Mapped[List['Produccion']] = relationship(
        'Produccion', back_populates='lote_galleta')
    merma: Mapped[List['Merma']] = relationship('Merma', back_populates='lote_galleta')


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

    id_receta_insumo: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad_insumo: Mapped[float] = mapped_column(Float)
    id_receta: Mapped[Optional[int]] = mapped_column(Integer)
    id_insumo: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    insumo: Mapped[Optional['Insumo']] = relationship(
        'Insumo', back_populates='receta_insumo')
    receta: Mapped[Optional['Receta']] = relationship(
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

    id_detalle: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Float)
    tipo_venta: Mapped[str] = mapped_column(String(50))
    id_venta: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_galleta: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Mapped[Optional['LoteGalleta']] = relationship(
        'LoteGalleta', back_populates='detalle_venta')
    venta: Mapped[Optional['Venta']] = relationship(
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

    id_produccion: Mapped[int] = mapped_column(Integer, primary_key=True)
    estatus: Mapped[str] = mapped_column(String(100))
    id_usuario: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_galleta: Mapped[Optional[int]] = mapped_column(Integer)
    id_receta: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Mapped[Optional['LoteGalleta']] = relationship(
        'LoteGalleta', back_populates='produccion')
    receta: Mapped[Optional['Receta']] = relationship(
        'Receta', back_populates='produccion')
    usuario: Mapped[Optional['usuario']] = relationship(
        'usuario', back_populates='produccion')
    merma: Mapped[List['Merma']] = relationship('Merma', back_populates='produccion')
    produccion_insumo: Mapped[List['ProduccionInsumo']] = relationship(
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

    id_merma: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_merma: Mapped[str] = mapped_column(String(50))
    cantidad: Mapped[float] = mapped_column(Float)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime)
    id_produccion: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_insumo: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_galleta: Mapped[Optional[int]] = mapped_column(Integer)
    motivo: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_galleta: Mapped[Optional['LoteGalleta']] = relationship(
        'LoteGalleta', back_populates='merma')
    lote_insumo: Mapped[Optional['LoteInsumo']] = relationship(
        'LoteInsumo', back_populates='merma')
    produccion: Mapped[Optional['Produccion']] = relationship(
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

    id_produccion_insumo: Mapped[int] = mapped_column(Integer, primary_key=True)
    cantidad_usada: Mapped[float] = mapped_column(Float)
    id_produccion: Mapped[Optional[int]] = mapped_column(Integer)
    id_lote_insumo: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    lote_insumo: Mapped[Optional['LoteInsumo']] = relationship(
        'LoteInsumo', back_populates='produccion_insumo')
    produccion: Mapped[Optional['Produccion']] = relationship(
        'Produccion', back_populates='produccion_insumo')
