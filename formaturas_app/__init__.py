from flask import Flask, send_from_directory, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, logout_user
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    from datetime import date, timedelta
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///formaturas.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Importa os modelos para registrar os callbacks do Flask-Login e utilizar os enums necessários
    from formaturas_app import models
    from formaturas_app.models import StatusEnum  # Usado na verificação do status da empresa

    # Registro dos blueprints
    from formaturas_app.auth.routes import auth_bp
    from formaturas_app.auth.perfil import perfil_bp
    from formaturas_app.empresa.routes import empresa_bp
    from formaturas_app.home.routes import home_bp
    from formaturas_app.turmas.routes import turmas_bp
    from formaturas_app.relatorios.routes import relatorios_bp 
    from formaturas_app.equipe.routes import equipe_bp  # Inclui rota de cadastro na equipe

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(perfil_bp, url_prefix='/auth')  
    app.register_blueprint(empresa_bp, url_prefix='/empresa')
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(turmas_bp, url_prefix='/turmas')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')   
    app.register_blueprint(equipe_bp, url_prefix='/equipe')  

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'img'),
            'favicon.svg', mimetype='image/svg+xml'
        )

    with app.app_context():
        db.create_all()
        # Importa e executa o seed para o admin, se necessário
        from formaturas_app.seed import seed_admin
        seed_admin()
    
    # Adiciona uma verificação global antes de cada requisição
    @app.before_request
    def check_company_status():
        # Se o usuário estiver autenticado, verifica se a empresa está ativa.
        if current_user.is_authenticated:
            # Caso a empresa esteja inativa, encerra a sessão e redireciona para o login com uma mensagem
            if current_user.empresa.status != StatusEnum.ATIVA:
                logout_user()
                flash("Sua empresa está inativa. Entre em contato com o administrador ou regularize sua assinatura.", "danger")
                return redirect(url_for("auth.login"))
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app
