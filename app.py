from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, Proveedor, db
from forms_compras import InsumoForm, ProveedorForm
from routes.insumos import insumo_bp
from routes.proveedores import proveedor_bp
from routes.compras import compras_bp

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
db.init_app(app)

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/index", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

app.register_blueprint(insumo_bp)
app.register_blueprint(proveedor_bp)
app.register_blueprint(compras_bp, url_prefix='/compras')







if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)