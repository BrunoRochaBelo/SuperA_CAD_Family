from flask import Blueprint, render_template, request, redirect, url_for, flash
from formaturas_app.models import Empresa, Usuario, PapelEnum
from formaturas_app import db
import datetime

empresa_bp = Blueprint('empresa', __name__)

@empresa_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_empresa():
    """
    Rota para cadastro de uma nova empresa e criação do usuário administrador associado.
    O cadastro inclui: nome da empresa, email e senha do administrador,
    limite de usuários (opcional) e data de expiração da assinatura (opcional).
    """
    if request.method == 'POST':
        nome_empresa = request.form.get('nome_empresa')
        email_admin = request.form.get('email_admin')
        senha_admin = request.form.get('senha_admin')
        max_usuarios = request.form.get('max_usuarios')
        assinatura_ativa_ate_str = request.form.get('assinatura_ativa_ate')
        
        # Validação básica – campos obrigatórios
        if not nome_empresa or not email_admin or not senha_admin:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for('empresa.cadastrar_empresa'))
        
        try:
            max_usuarios = int(max_usuarios) if max_usuarios else 5
        except:
            max_usuarios = 5

        try:
            if assinatura_ativa_ate_str:
                assinatura_ativa_ate = datetime.datetime.strptime(assinatura_ativa_ate_str, '%Y-%m-%d').date()
            else:
                assinatura_ativa_ate = datetime.date.today() + datetime.timedelta(days=30)
        except:
            assinatura_ativa_ate = datetime.date.today() + datetime.timedelta(days=30)
        
        # Checa se já existe uma empresa com o mesmo nome
        if Empresa.query.filter_by(nome=nome_empresa).first():
            flash("Já existe uma empresa com esse nome.", "danger")
            return redirect(url_for('empresa.cadastrar_empresa'))
        
        # Cria a empresa
        nova_empresa = Empresa(
            nome=nome_empresa,
            assinatura_ativa_ate=assinatura_ativa_ate,
            max_usuarios=max_usuarios
        )
        db.session.add(nova_empresa)
        db.session.commit()

        # Cria o usuário administrador associado à empresa cadastrada
        admin = Usuario(
            email=email_admin,
            nome="Administrador",
            papel=PapelEnum.ADM,
            empresa_id=nova_empresa.id
        )
        admin.set_password(senha_admin)
        db.session.add(admin)
        db.session.commit()

        flash("Empresa e usuário administrador cadastrados com sucesso!", "success")
        # Redireciona para a página de login após o cadastro da empresa
        return redirect(url_for('auth.login'))
    
    return render_template('empresa/register.html')
