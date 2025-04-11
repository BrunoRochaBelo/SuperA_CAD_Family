from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///formaturas.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Registro dos blueprints
    from formaturas_app.auth.routes import auth_bp
    from formaturas_app.home.routes import home_bp
    from formaturas_app.turmas.routes import turmas_bp
    from formaturas_app.relatorios.routes import relatorios_bp 

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(turmas_bp, url_prefix='/turmas')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')   

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                                   'favicon.svg', mimetype='image/svg+xml')

    # Criação das tabelas se elas não existirem
    with app.app_context():
        from formaturas_app import models
        db.create_all()

    # Adiciona teardown para limpar a sessão ao final de cada request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app
