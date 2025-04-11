from formaturas_app import create_app, db
from formaturas_app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    if not Usuario.query.filter_by(nome='admin').first():
        admin = Usuario(nome='admin', senha_hash=generate_password_hash('1234'), papel='ADM')
        editor = Usuario(nome='editor', senha_hash=generate_password_hash('1234'), papel='EDITOR')
        viewer = Usuario(nome='visualizador', senha_hash=generate_password_hash('1234'), papel='VISUALIZADOR')
        db.session.add_all([admin, editor, viewer])
        db.session.commit()
        print("Usuários criados: admin, editor, visualizador (senha: 1234)")
    else:
        print("Usuários já existem. Nenhuma ação tomada.")
