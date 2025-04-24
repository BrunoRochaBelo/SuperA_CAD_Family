from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from formaturas_app.models import PapelEnum, Usuario
from formaturas_app import db

equipe_bp = Blueprint('equipe', __name__)

@equipe_bp.route('/')
@login_required
def index():
    # — Mostra só a galera da empresa do ADM logado
    users = (
        Usuario.query
               .filter_by(empresa_id=current_user.empresa_id)
               .all()
    )
    return render_template('equipe/index.html', users=users, active_page='equipe')


@equipe_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    # Só ADM pode criar gente
    if current_user.papel_str != 'ADM':
        flash("Acesso não autorizado!", "danger")
        return redirect(url_for('equipe.index'))
    
    if request.method == 'POST':
        nome  = request.form.get('nome')
        email = request.form.get('email', '').lower()
        papel = request.form.get('papel')
        
        # Evita duplicar e-mail na MESMA empresa
        usuario_existente = (
            Usuario.query
                   .filter_by(email=email, empresa_id=current_user.empresa_id)
                   .first()
        )
        if usuario_existente:
            flash("E-mail já cadastrado nessa empresa. Use outro!", "danger")
            return redirect(url_for('equipe.cadastrar_usuario'))
        
        # Cria o usuário e já amarra na empresa certa
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            papel=PapelEnum(papel),
            empresa_id=current_user.empresa_id
        )
        novo_usuario.set_password("default123")  # senha inicial

        db.session.add(novo_usuario)
        db.session.commit()
        
        flash("Usuário criado com sucesso! Senha padrão: default123", "success")
        return redirect(url_for('equipe.index'))
    
    return render_template('equipe/cadastro.html', active_page='equipe')


@equipe_bp.route('/editar_usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    data = request.get_json() or {}
    # Busca só na própria empresa
    user = (
        Usuario.query
               .filter_by(id=user_id, empresa_id=current_user.empresa_id)
               .first()
    )
    if not user:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado ou não é da sua empresa'
        }), 404

    # Protege o admin master
    if user.email.lower() == "adminbruno@diretiva.com":
        return jsonify({
            'success': False,
            'message': 'Não é permitido alterar o admin do sistema.'
        }), 403

    # Atualiza campos
    user.nome  = data.get('nome', user.nome)
    user.papel = PapelEnum(data.get('papel', user.papel.value))
    db.session.commit()
    return jsonify({'success': True})


@equipe_bp.route('/excluir_usuario/<int:user_id>', methods=['DELETE'])
@login_required
def excluir_usuario(user_id):
    # Só exclui se for da mesma empresa
    user = (
        Usuario.query
               .filter_by(id=user_id, empresa_id=current_user.empresa_id)
               .first()
    )
    if not user:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado ou não é da sua empresa'
        }), 404

    # Protege o admin master
    if user.email.lower() == "adminbruno@diretiva.com":
        return jsonify({
            'success': False,
            'message': 'Não é permitido excluir o admin do sistema.'
        }), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})


@equipe_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    # API que devolve só a galera da empresa do cara logado
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
