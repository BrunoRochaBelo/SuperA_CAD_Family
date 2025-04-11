# formaturas_app/auth/perfil.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from formaturas_app import db
from formaturas_app.models import Usuario
from flask import jsonify


perfil_bp = Blueprint('perfil', __name__)

# Extensões permitidas para upload de imagens
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Verifica se o arquivo possui uma extensão permitida (imagem)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@perfil_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """
    Rota para edição do perfil do usuário.
    Permite atualizar:
      - Nome completo,
      - Nome de usuário (com verificação de duplicidade),
      - Foto de perfil (upload, que sobrescreve a foto existente).
    """
    if request.method == 'POST':
        nome = request.form.get("nome")
        username = request.form.get("username")
        
        if nome:
            current_user.nome = nome
        
        if username:
            # Verifica se o nome de usuário já está em uso por outro usuário
            existing_user = Usuario.query.filter(Usuario.username == username, Usuario.id != current_user.id).first()
            if existing_user:
                flash("Nome de usuário já está em uso. Escolha outro.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
            current_user.username = username
        
        # Processa o upload da nova foto de perfil, se enviado
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Utiliza um prefixo com o ID do usuário para evitar conflitos e garantir a substituição
                filename = f"user_{current_user.id}_" + filename
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'fotos')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                # Atualiza o campo com o caminho relativo à pasta static
                current_user.foto_perfil = f"uploads/fotos/{filename}"
            elif file and file.filename != "":
                flash("Arquivo não permitido. Utilize png, jpg, jpeg ou gif.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
        
        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar o perfil: " + str(e), "danger")
        return redirect(url_for("perfil.editar_perfil"))
    
    return render_template("auth/editar_perfil.html", usuario=current_user)

@perfil_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    """
    Rota para alteração de senha.
    Recebe via POST: senha atual, nova senha e confirmação da nova senha.
    Se a senha atual estiver incorreta ou as novas não conferirem, exibe mensagem de erro.
    """
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    if not current_user.check_password(current_password):
        flash("Senha atual incorreta!", "danger")
        return redirect(url_for("perfil.editar_perfil"))
    
    if new_password != confirm_password:
        flash("As novas senhas não conferem!", "danger")
        return redirect(url_for("perfil.editar_perfil"))
    
    current_user.set_password(new_password)
    try:
        db.session.commit()
        flash("Senha alterada com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Erro ao alterar a senha: " + str(e), "danger")
    
    return redirect(url_for("perfil.editar_perfil"))

@perfil_bp.route('/validar_senha', methods=['POST'])
@login_required
def validar_senha():
    """
    Endpoint para validação da senha atual via AJAX.
    Recebe um JSON com a senha atual e retorna {"valid": True} ou {"valid": False}.
    """
    data = request.get_json()
    current_password = data.get("current_password")
    
    if current_password and current_user.check_password(current_password):
        return jsonify(valid=True)
    else:
        return jsonify(valid=False)

