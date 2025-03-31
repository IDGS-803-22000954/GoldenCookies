from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Insumo, db
from forms_compras import InsumoForm
from venta import venta
from pedidos import pedidos

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
db.init_app(app)

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    formulario = InsumoForm()
    
    if formulario.validate_on_submit():
        nuevo_insumo = Insumo(
            nombre=formulario.nombre.data,
            unidad_medida=formulario.unidad_medida.data,
            cantidad_insumo=formulario.cantidad_insumo.data
        )
        db.session.add(nuevo_insumo)
        db.session.commit()
        flash('Insumo agregado correctamente!', 'success')
        return redirect(url_for('index'))
    
    return render_template('index.html', formulario=formulario)

app.register_blueprint(venta)
app.register_blueprint(pedidos)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)