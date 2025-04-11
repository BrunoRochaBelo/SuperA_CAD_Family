from formaturas_app import db
from formaturas_app.models import Usuario, Empresa, PapelEnum
import datetime

def criar_admin():
    """
    Cria uma empresa de testes e um usuário administrador para desenvolvimento.
    A empresa 'Demo Company' terá uma assinatura ativa por 30 dias a partir de hoje.
    """
    empresa_nome = "Demo Company"
    empresa = Empresa.query.filter_by(nome=empresa_nome).first()
    if not empresa:
        empresa = Empresa(
            nome=empresa_nome,
            assinatura_ativa_ate=datetime.date.today() + datetime.timedelta(days=30)
        )
        db.session.add(empresa)
        db.session.commit()

    admin_email = "admin@demo.com"
    admin = Usuario.query.filter_by(email=admin_email).first()
    if not admin:
        admin = Usuario(
            email=admin_email,
            nome="Administrador",
            papel=PapelEnum.ADM,
            empresa_id=empresa.id
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Usuário administrador criado com sucesso!")
    else:
        print("Usuário administrador já existe.")

if __name__ == "__main__":
    from formaturas_app import create_app
    app = create_app()
    with app.app_context():
        criar_admin()
