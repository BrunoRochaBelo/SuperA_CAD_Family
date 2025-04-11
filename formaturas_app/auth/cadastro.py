# formaturas_app/auth/cadastro.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from formaturas_app.models import Usuario, PapelEnum
from formaturas_app import db
from formaturas_app.utils.helpers import get_limite_empresa

cadastro_bp = Blueprint("cadastro", __name__)

@cadastro_bp.route("/cadastrar_usuario", methods=["GET", "POST"])
@login_required
def cadastrar_usuario():
    """
    Rota para cadastro de novos usuários.
    Apenas usuários com papel ADM podem cadastrar novos usuários para a empresa.
    Verifica se o limite de usuários (por empresa) já foi atingido.
    """
    # Verifica se o usuário logado é ADM
    if current_user.papel != PapelEnum.ADM:
        flash("Apenas administradores podem cadastrar usuários.", "danger")
        return redirect(url_for("home.index"))
        
    if request.method == "POST":
        # Obtém os dados do formulário
        email = request.form.get("email")
        nome = request.form.get("nome")
        senha = request.form.get("senha")
        papel_str = request.form.get("papel")  # Deve ser "ADM", "EDITOR" ou "VISUALIZADOR"

        # Validação básica de entrada
        if not email or not nome or not senha or not papel_str:
            flash("Todos os campos são obrigatórios.", "danger")
            return redirect(url_for("cadastro.cadastrar_usuario"))
        
        # Verifica se já existe um usuário com este email para a empresa
        usuario_existente = Usuario.query.filter_by(email=email, empresa_id=current_user.empresa_id).first()
        if usuario_existente:
            flash("Já existe um usuário cadastrado com este email para sua empresa.", "danger")
            return redirect(url_for("cadastro.cadastrar_usuario"))
        
        # Verifica se o limite de usuários já foi atingido
        total_usuarios = Usuario.query.filter_by(empresa_id=current_user.empresa_id).count()
        limite = get_limite_empresa(current_user.empresa)
        if total_usuarios >= limite:
            flash("Limite de usuários atingido para sua empresa.", "danger")
            return redirect(url_for("cadastro.cadastrar_usuario"))
        
        # Cria o novo usuário associado à empresa do administrador
        novo_usuario = Usuario(
            email=email,
            nome=nome,
            papel=PapelEnum(papel_str),
            empresa_id=current_user.empresa_id
        )
        novo_usuario.set_password(senha)
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Usuário cadastrado com sucesso!", "success")
        return redirect(url_for("home.index"))
        
    # Para método GET, apenas renderiza o formulário de cadastro
    return render_template("auth/register.html")
