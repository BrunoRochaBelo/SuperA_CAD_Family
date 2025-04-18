import os
import base64
from io import BytesIO
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, jsonify
)
from flask_login import login_required, current_user
from formaturas_app import db, limiter
from formaturas_app.models import Usuario
from formaturas_app.decorators import require_trusted_origin
from formaturas_app.utils.loggers import log_audit, log_access
from markupsafe import escape
from PIL import Image

perfil_bp = Blueprint('perfil', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@perfil_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """
    Edita nome, username e foto de perfil do usuário.
    """
    if request.method == 'POST':
        nome = request.form.get("nome")
        username = request.form.get("username")
        
        if nome:
            current_user.nome = escape(nome.strip())
        if username:
            cleaned = escape(username.strip())
            if '<' in cleaned or '>' in cleaned:
                flash("O nome de usuário contém caracteres inválidos.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
            exists = Usuario.query.filter(
                Usuario.username == cleaned,
                Usuario.id != current_user.id
            ).first()
            if exists:
                flash("Nome de usuário já está em uso. Escolha outro.", "danger")
                return redirect(url_for("perfil.editar_perfil"))
            current_user.username = cleaned

        # processa foto
        try:
            if request.form.get('delete_photo') == 'true':
                if current_user.foto_perfil:
                    old = os.path.join(current_app.root_path, 'static', current_user.foto_perfil)
                    if os.path.exists(old):
                        os.remove(old)
                    current_user.foto_perfil = None

            elif cropped := request.form.get('cropped_image_data'):
                if not cropped.startswith('data:image/'):
                    flash("Formato de imagem inválido.", "danger")
                    return redirect(url_for("perfil.editar_perfil"))

                fmt, imgstr = cropped.split(';base64,')
                ext = fmt.split('/')[-1]
                if ext.lower() not in ALLOWED_EXTENSIONS:
                    flash("Formato de imagem não permitido.", "danger")
                    return redirect(url_for("perfil.editar_perfil"))

                data = base64.b64decode(imgstr)
                img = Image.open(BytesIO(data))
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'fotos')
                os.makedirs(upload_folder, exist_ok=True)
                filename = f"user_{current_user.id}.{ext}"
                path = os.path.join(upload_folder, filename)

                # remove antigo
                if current_user.foto_perfil:
                    old = os.path.join(current_app.root_path, 'static', current_user.foto_perfil)
                    if os.path.exists(old) and old != path:
                        os.remove(old)

                bio = BytesIO()
                if ext.lower() in ('jpg', 'jpeg'):
                    img.convert('RGB').save(bio, format='JPEG', quality=85, optimize=True)
                else:
                    img.save(bio, format=ext.upper())
                bio.seek(0)
                with open(path, 'wb') as f:
                    f.write(bio.getvalue())

                current_user.foto_perfil = f"uploads/fotos/{filename}"

        except Exception as e:
            flash(f"Erro ao processar a foto: {e}", "danger")
            log_audit(f"Erro ao processar foto de perfil: {e}")
            return redirect(url_for("perfil.editar_perfil"))

        # grava alterações no DB
        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            log_access("Perfil atualizado com sucesso")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar o perfil: {e}", "danger")
            log_audit(f"Falha ao atualizar perfil: {e}")

        return redirect(url_for("perfil.editar_perfil"))

    return render_template(
        "auth/editar_perfil.html",
        usuario=current_user,
        active_page="editar_perfil"
    )


@perfil_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    current_password = request.form.get("current_password")
    new_password     = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not current_user.check_password(current_password):
        flash("Senha atual incorreta!", "danger")
        log_audit("Senha atual incorreta")
        return redirect(url_for("perfil.editar_perfil"))

    if new_password != confirm_password:
        flash("As novas senhas não conferem!", "danger")
        log_audit("Nova senha e confirmação não conferem")
        return redirect(url_for("perfil.editar_perfil"))

    current_user.set_password(new_password)
    try:
        db.session.commit()
        flash("Senha alterada com sucesso!", "success")
        log_audit("Senha alterada com sucesso")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao alterar a senha: {e}", "danger")
        log_audit(f"Erro ao alterar senha: {e}")

    return redirect(url_for("perfil.editar_perfil"))


@perfil_bp.route('/validar_senha', methods=['POST'])
@limiter.limit("5 per minute")
@require_trusted_origin()
@login_required
def validar_senha():
    data = request.get_json() or {}
    pwd  = data.get("current_password", "")

    if current_user.check_password(pwd):
        log_audit("Validação de senha bem‑sucedida")
        return jsonify(valid=True)
    else:
        log_audit("Validação de senha falhou")
        return jsonify(valid=False)
