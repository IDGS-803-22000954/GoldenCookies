from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, usuario, db
from forms_compras import InsumoForm
from venta import venta
from pedidos import pedidos
from auth import auth
from routes.insumos import insumo_bp
from routes.proveedores import proveedor_bp
from routes.compras import compras_bp
from produccion.routes import produccion_bp
from recetas.recetas import recetas_bp
from recetas.galletas import galletas_bp

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
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

    return redirect('auth/login')


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')


@app.route('/produccion')
@login_required
def produccion():
    return render_template('produccion.html')


@app.route('/cliente')
@login_required
def cliente():
    return render_template('cliente.html')


app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(insumo_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(compras_bp, url_prefix='/compras')
app.register_blueprint(venta)
app.register_blueprint(pedidos)
app.register_blueprint(produccion_bp, url_prefix='/produccion')
app.register_blueprint(recetas_bp, url_prefix='/recetas')
app.register_blueprint(galletas_bp, url_prefix='/galletas')

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    app.register_error_handler(401, status_401)
    with app.app_context():
        db.create_all()
    app.run()
