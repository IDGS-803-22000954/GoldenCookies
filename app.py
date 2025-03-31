import os
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from flask import flash
from functools import wraps
from flask import abort
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, request, redirect, url_for, session
from config import DevelopmentConfig 
from flask import g
from models import db
from models import usuario
from auth import auth 

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
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

app.register_blueprint(auth, url_prefix='/auth')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Ruta de inicio de sesión

@login_manager.user_loader
def load_user(user_id):
    return usuario.query.get(int(user_id)) 

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/produccion')
def produccion():
    return render_template('produccion.html')

@app.route('/cliente')
def cliente():
    return render_template('cliente.html')

@app.route('/venta')
def venta():
    return render_template('venta.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def status_401(error):
    return redirect(url_for('login'))


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    app.register_error_handler(401,status_401)
    with app.app_context():
        db.create_all()
    app.run()
