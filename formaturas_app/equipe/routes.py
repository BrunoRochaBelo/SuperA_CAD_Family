from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from formaturas_app.models import PapelEnum, Usuario
from formaturas_app import db

equipe_bp = Blueprint('equipe', __name__)

@equipe_bp.route('/')
@login_required
def index():
    users = Usuario.query.all()
    return render_template('equipe/index.html', users=users, active_page='equipe')

@equipe_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if current_user.papel_str != 'ADM':
        flash("Acesso não autorizado!", "error")
        return redirect(url_for('equipe.index'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        papel = request.form.get('papel')
        
        novo_usuario = Usuario(nome=nome, email=email, papel=PapelEnum(papel))
        # Define uma senha padrão para o usuário (pode ser alterada depois)
        novo_usuario.set_password("default123")
        # Associa o novo usuário à empresa do ADM logado
        novo_usuario.empresa_id = current_user.empresa_id
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash("Usuário cadastrado com sucesso! A senha padrão é: default123", "success")
        return redirect(url_for('equipe.index'))
    
    return render_template('equipe/cadastro.html', active_page='equipe')

@equipe_bp.route('/editar_usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    data = request.get_json()
    user = Usuario.query.get(user_id)
    if user:
        user.nome = data.get('nome')
        user.papel = PapelEnum(data.get('papel'))
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})

@equipe_bp.route('/excluir_usuario/<int:user_id>', methods=['DELETE'])
@login_required
def excluir_usuario(user_id):
    user = Usuario.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})

@equipe_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    users = Usuario.query.all()
    users_data = [{
        'id': user.id,
        'nome': user.nome,
        'email': user.email,
        'papel_str': user.papel.value
    } for user in users]
    summary = {
        'total_users': len(users),
        'total_adm': len([u for u in users if u.papel.value == 'ADM']),
        'total_editor': len([u for u in users if u.papel.value == 'EDITOR']),
        'total_visualizador': len([u for u in users if u.papel.value == 'VISUALIZADOR']),
    }
    return jsonify({'users': users_data, 'summary': summary})
