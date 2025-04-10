from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, usuario, db
from auth import auth
from routes.insumos import insumo_bp
from routes.proveedores import proveedor_bp
from routes.compras import compras_bp
from auth import verificar_roles
from venta import venta
from recetas.recetas import recetas_bp
from produccion.routes import produccion_bp
from routes.catalogo import catalogo_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Ruta de inicio de sesión


@login_manager.user_loader
def load_user(user_id):
    return usuario.query.get(int(user_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def status_401(error):
    return redirect(url_for('login'))


@app.route("/")
@app.route("/index")
def index():

    return redirect('catalogo')


@app.route('/admin')
@login_required
@verificar_roles('admin')
def admin():
    return redirect(url_for('dashboard.index'))

@app.route('/cliente')
@verificar_roles('cliente','admin')
@login_required
def cliente():
    return redirect('catalogo')

@app.route("/menu")
@login_required
@verificar_roles('admin')
def menu():
    return render_template('admin.html')


app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(insumo_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(compras_bp, url_prefix='/compras')
app.register_blueprint(venta, url_prefix='/venta')
app.register_blueprint(recetas_bp, url_prefix='/recetas')
app.register_blueprint(produccion_bp, url_prefix='/produccion')
app.register_blueprint(catalogo_bp, url_prefix='/catalogo')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    app.register_error_handler(401, status_401)
    with app.app_context():
        db.create_all()
    app.run()
