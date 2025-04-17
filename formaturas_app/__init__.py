import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_from_directory, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Extensões globais
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
limiter = Limiter(key_func=get_remote_address)


def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Configurações básicas
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///formaturas.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Configura loggers separados
    setup_loggers(app)

    # Importa modelos (callback do Flask-Login, enums etc.)
    from formaturas_app import models
    from formaturas_app.models import StatusEnum

    # Importa e registra Blueprints
    from formaturas_app.auth.routes import auth_bp
    from formaturas_app.auth.perfil import perfil_bp
    from formaturas_app.empresa.routes import empresa_bp
    from formaturas_app.home.routes import home_bp
    from formaturas_app.turmas.routes import turmas_bp
    from formaturas_app.relatorios.routes import relatorios_bp
    from formaturas_app.equipe.routes import equipe_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(perfil_bp, url_prefix='/auth')
    app.register_blueprint(empresa_bp, url_prefix='/empresa')
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(turmas_bp, url_prefix='/turmas')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(equipe_bp, url_prefix='/equipe')

    # Rota de favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'img'),
            'favicon.svg', mimetype='image/svg+xml'
        )

    # Executa seed inicial com admin padrão
    with app.app_context():
        db.create_all()
        from formaturas_app.seed import seed_admin
        seed_admin()

    # Verifica se empresa está ativa antes de qualquer requisição
    @app.before_request
    def check_company_status():
        if current_user.is_authenticated:
            if current_user.empresa.status != StatusEnum.ATIVA:
                logout_user()
                flash("Sua empresa está inativa. Entre em contato com o administrador.", "danger")
                return redirect(url_for("auth.login"))

    # Finaliza conexão com o banco
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app


# 🔧 Loggers separados por tipo (access, crud, audit)
def setup_loggers(app):
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_config = [
        ('access', 'access.log'),
        ('crud', 'crud.log'),
        ('audit', 'audit.log'),
    ]

    for name, filename in log_config:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        file_path = os.path.join(logs_dir, filename)
        handler = RotatingFileHandler(file_path, maxBytes=1_000_000, backupCount=5)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s'
        ))

        if not logger.hasHandlers():
            logger.addHandler(handler)

    app.logger.info("Loggers configurados com sucesso.")
