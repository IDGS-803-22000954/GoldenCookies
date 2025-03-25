from flask import Flask, render_template, request, redirect, url_for, session
from flask import flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask import g
import forms_compras
from models import Insumo
from models import db
from forms_compras import InsumoForm

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf=CSRFProtect()

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

@app.route('/agregar_insumo', methods=['GET', 'POST'])
def agregar_insumo():
    formulario = InsumoForm()  # Cambiado de 'form' a 'formulario'
    
    if formulario.validate_on_submit():
        nuevo_insumo = Insumo(
            nombre=formulario.nombre.data,
            unidad_medida=formulario.unidad_medida.data
        )
        db.session.add(nuevo_insumo)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('index.html', formulario=formulario)



if __name__ == '__main__':
	app.run(debug=True)