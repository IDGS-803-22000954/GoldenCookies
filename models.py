from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
db = SQLAlchemy()


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

# goldenAdN--admin
# goldenVdN--vendedor
# goldenPrN--produccion
#Tiger8431
#LunarX27
#Gadget9023
#Bravo55Z