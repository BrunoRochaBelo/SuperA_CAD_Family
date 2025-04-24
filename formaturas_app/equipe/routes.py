from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from formaturas_app.models import PapelEnum, Usuario
from formaturas_app import db

equipe_bp = Blueprint('equipe', __name__)

@equipe_bp.route('/')
@login_required
def index():
    users = (
        Usuario.query
               .filter_by(empresa_id=current_user.empresa_id)
               .all()
    )
    return render_template('equipe/index.html', users=users, active_page='equipe')


@equipe_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    # Só ADM pode criar usuários
    if current_user.papel_str != 'ADM':
        flash("Acesso não autorizado!", "danger")
        return redirect(url_for('equipe.index'))
    
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        papel = request.form.get('papel')

        # 1) Verificação global de e-mail
        if Usuario.query.filter_by(email=email).first():
            flash("E-mail já cadastrado no sistema. Use outro!", "danger")
            return redirect(url_for('equipe.cadastrar_usuario'))
        
        # Se quiser manter aquela verificação por empresa, dá pra checar aqui também:
        # if Usuario.query.filter_by(email=email, empresa_id=current_user.empresa_id).first():
        #     flash("E-mail já cadastrado nessa empresa. Use outro!", "danger")
        #     return redirect(url_for('equipe.cadastrar_usuario'))

        # 2) Cria o usuário e vincula à empresa
        novo = Usuario(
            nome=nome,
            email=email,
            papel=PapelEnum(papel),
            empresa_id=current_user.empresa_id
        )
        novo.set_password("default123")

        db.session.add(novo)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("E-mail já cadastrado no sistema. Use outro!", "danger")
            return redirect(url_for('equipe.cadastrar_usuario'))

        flash("Usuário criado com sucesso! Senha padrão: default123", "success")
        return redirect(url_for('equipe.index'))
    
    return render_template('equipe/cadastro.html', active_page='equipe')


@equipe_bp.route('/editar_usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    data = request.get_json() or {}
    user = (
        Usuario.query
               .filter_by(id=user_id, empresa_id=current_user.empresa_id)
               .first()
    )
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado ou não é da sua empresa'}), 404

    if user.email.lower() == "adminbruno@diretiva.com":
        return jsonify({'success': False, 'message': 'Não é permitido alterar o admin do sistema.'}), 403

    user.nome  = data.get('nome', user.nome)
    user.papel = PapelEnum(data.get('papel', user.papel.value))
    db.session.commit()
    return jsonify({'success': True})


@equipe_bp.route('/excluir_usuario/<int:user_id>', methods=['DELETE'])
@login_required
def excluir_usuario(user_id):
    user = (
        Usuario.query
               .filter_by(id=user_id, empresa_id=current_user.empresa_id)
               .first()
    )
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado ou não é da sua empresa'}), 404

    if user.email.lower() == "adminbruno@diretiva.com":
        return jsonify({'success': False, 'message': 'Não é permitido excluir o admin do sistema.'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})


@equipe_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    users = (
        Usuario.query
               .filter_by(empresa_id=current_user.empresa_id)
               .all()
    )
    users_data = [{
        'id':       u.id,
        'nome':     u.nome,
        'email':    u.email,
        'papel_str': u.papel.value
    } for u in users]

    summary = {
        'total_users':       len(users),
        'total_adm':         sum(1 for u in users if u.papel == PapelEnum.ADM),
        'total_editor':      sum(1 for u in users if u.papel == PapelEnum.EDITOR),
        'total_visualizador':sum(1 for u in users if u.papel == PapelEnum.VISUALIZADOR),
    }

    return jsonify({'users': users_data, 'summary': summary})
