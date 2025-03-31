from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from flask import flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask import g
from models import db
#from flask_login import LoginManager, login_user, logout_user, login_reqd
import json

from config import DevelopmentConfig

from recetas.recetas import recetas_bp
from recetas.galletas import galletas_bp

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
db.init_app(app)




app.register_blueprint(galletas_bp, url_prefix='/galletas')  # Agregado
app.register_blueprint(recetas_bp, url_prefix='/recetas')   


@app.route("/", methods=['GET', 'POST'])
def home():
    return redirect(url_for('index'))	

	
@app.route("/index", methods=['GET', 'POST'])
def index():
    """Página de inicio"""
    return render_template('index.html')


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True)

