from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, Proveedor, db
from forms_compras import InsumoForm, ProveedorForm
from routes.insumos import insumo_bp
from routes.proveedores import proveedor_bp
from routes.compras import compras_bp
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from flask import flash
from functools import wraps
from flask import abort
from flask import g
from models import usuario
from auth import auth 
import os

def role_required(role_id):
    """ Decorador para restringir acceso según el id_rol del usuario """
    def decorator(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.id_rol != role_id:
                abort(404)  # Mostrar error 404 en lugar de redirigir a login
            return f(*args, **kwargs)
        return wrapped_function
    return decorator


app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

app.register_blueprint(insumo_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(compras_bp, url_prefix='/compras')

if __name__ == '__main__':
	app.run(debug=True)