# formaturas_app/seed.py
from formaturas_app.models import db, Empresa, Usuario, PapelEnum, StatusEnum
from datetime import date, timedelta

def seed_admin():
    admin_email = "adminbruno@diretiva.com"
    # Converte o email para lowercase para ficar consistente
    admin_user = Usuario.query.filter_by(email=admin_email.lower()).first()
    if not admin_user:
        # Verifica se já existe uma empresa para a administração do sistema
        admin_empresa = Empresa.query.filter_by(nome="Administração do Sistema").first()
        if not admin_empresa:
            admin_empresa = Empresa(
                nome="Administração do Sistema",
                assinatura_ativa_ate=date.today() + timedelta(days=365),
                max_usuarios=9999,
                status=StatusEnum.ATIVA
            )
            db.session.add(admin_empresa)
            db.session.commit()  # Importante para garantir que o admin_empresa receba um ID
        # Cria o usuário administrador do sistema
        admin_user = Usuario(
            email=admin_email,
            nome="Desenvolvedor",
            papel=PapelEnum.ADM,
            empresa_id=admin_empresa.id
        )
        admin_user.set_password("DevDiretiva")
        db.session.add(admin_user)
        db.session.commit()
