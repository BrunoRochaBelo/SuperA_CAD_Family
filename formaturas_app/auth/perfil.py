# arquivo perfil.py

import os
import base64
import re
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from formaturas_app import db
from formaturas_app.models import Usuario
from markupsafe import escape
from PIL import Image

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
      - Nome de usuário (com verificação de duplicidade e sanitização),
      - Foto de perfil (upload, com validação adicional da imagem).
    """
    if request.method == 'POST':
        nome = request.form.get("nome")
        username = request.form.get("username")
        
        # Sanitiza e valida os inputs para evitar scripts injetados
        if nome:
            nome = escape(nome.strip())
            current_user.nome = nome
        
        if username:
            username = escape(username.strip())
            if '<' in username or '>' in username:
                flash("O nome de usuário contém caracteres inválidos.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
            
            # Verifica se o nome de usuário já está em uso por outro usuário
            existing_user = Usuario.query.filter(Usuario.username == username, Usuario.id != current_user.id).first()
            if existing_user:
                flash("Nome de usuário já está em uso. Escolha outro.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
            current_user.username = username
        
        # Nova implementação para processar a imagem enviada pelo editor
        try:
            # Verifica se o usuário solicitou a exclusão da foto
            if 'delete_photo' in request.form and request.form.get('delete_photo') == 'true':
                # Exclui a foto atual se existir
                if current_user.foto_perfil:
                    old_photo_path = os.path.join(current_app.root_path, 'static', current_user.foto_perfil)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)
                    current_user.foto_perfil = None
            
            # Processa a imagem recortada, se enviada
            elif 'cropped_image_data' in request.form and request.form.get('cropped_image_data'):
                image_data = request.form.get('cropped_image_data')
                
                # Validar o formato dos dados da imagem
                if not image_data.startswith('data:image/'):
                    flash("Formato de imagem inválido.", "danger")
                    return redirect(url_for("perfil.editar_perfil"))
                
                # Extrair os dados da imagem
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Assegurar que a extensão é válida
                if ext.lower() not in ALLOWED_EXTENSIONS:
                    flash("Formato de imagem não permitido.", "danger")
                    return redirect(url_for("perfil.editar_perfil"))
                
                # Decodificar a imagem base64
                image_data = base64.b64decode(imgstr)
                
                # Salvar a imagem usando PIL para validação e potencial otimização
                try:
                    img = Image.open(BytesIO(image_data))
                    
                    # Preparar o diretório de upload
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'fotos')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    # Nome do arquivo baseado no ID do usuário para sobrescrever arquivos antigos
                    filename = f"user_{current_user.id}.{ext}"
                    filepath = os.path.join(upload_folder, filename)
                    
                    # Excluir a foto antiga se existir e for diferente
                    if current_user.foto_perfil:
                        old_photo_path = os.path.join(current_app.root_path, 'static', current_user.foto_perfil)
                        if os.path.exists(old_photo_path) and old_photo_path != filepath:
                            os.remove(old_photo_path)
                    
                    # Salvar a nova imagem
                    img_io = BytesIO()
                    
                    # Otimizar a qualidade da imagem para JPEG
                    if ext.lower() == 'jpeg' or ext.lower() == 'jpg':
                        img = img.convert('RGB')
                        img.save(img_io, format='JPEG', quality=85, optimize=True)
                    else:
                        img.save(img_io, format=ext.upper())
                    
                    img_io.seek(0)
                    with open(filepath, 'wb') as f:
                        f.write(img_io.getvalue())
                    
                    # Atualizar o caminho no banco de dados
                    current_user.foto_perfil = f"uploads/fotos/{filename}"
                    
                except Exception as e:
                    flash(f"Erro ao processar a imagem: {str(e)}", "danger")
                    return redirect(url_for("perfil.editar_perfil"))
        
        except Exception as e:
            flash(f"Erro ao processar a foto: {str(e)}", "danger")
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
    Recebe um JSON com a senha atual e retorna {"valid": True} se a senha estiver correta ou {"valid": False} caso contrário.
    """
    data = request.get_json()
    current_password = data.get("current_password")
    
    if current_password and current_user.check_password(current_password):
        return jsonify(valid=True)
    else:
        return jsonify(valid=False)
