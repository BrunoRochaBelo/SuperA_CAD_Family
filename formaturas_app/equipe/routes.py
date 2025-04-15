from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from formaturas_app.models import PapelEnum, Usuario
from formaturas_app import db

equipe_bp = Blueprint('equipe', __name__)

@equipe_bp.route('/')
@login_required
def index():
    # Filtra os usuários para exibir somente os da empresa do usuário logado
    users = Usuario.query.filter_by(empresa_id=current_user.empresa_id).all()
    return render_template('equipe/index.html', users=users, active_page='equipe')

@equipe_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if current_user.papel_str != 'ADM':
        flash("Acesso não autorizado!", "danger")
        return redirect(url_for('equipe.index'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email').lower()
        papel = request.form.get('papel')
        
        # Verifica se o e-mail já está cadastrado
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash("O e-mail informado já está cadastrado. Por favor, utilize outro!", "danger")
            return redirect(url_for('equipe.cadastrar_usuario'))
        
        novo_usuario = Usuario(nome=nome, email=email, papel=PapelEnum(papel))
        # Define uma senha padrão para o usuário (que pode ser alterada depois)
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
    # Filtra o usuário garantindo que ele pertence à mesma empresa do usuário logado
    user = Usuario.query.filter_by(id=user_id, empresa_id=current_user.empresa_id).first()
    if user:
        # Impede a alteração do administrador do sistema
        if user.email.lower() == "adminbruno@diretiva.com":
            return jsonify({'success': False, 'message': 'Não é permitido alterar o administrador do sistema.'})
        user.nome = data.get('nome')
        user.papel = PapelEnum(data.get('papel'))
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado ou não pertence à sua empresa'
        })

@equipe_bp.route('/excluir_usuario/<int:user_id>', methods=['DELETE'])
@login_required
def excluir_usuario(user_id):
    # Verifica se o usuário a ser excluído pertence à mesma empresa do usuário logado
    user = Usuario.query.filter_by(id=user_id, empresa_id=current_user.empresa_id).first()
    if user:
        # Impede a exclusão do administrador do sistema
        if user.email.lower() == "adminbruno@diretiva.com":
            return jsonify({'success': False, 'message': 'Não é permitido excluir o administrador do sistema.'})
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado ou não pertence à sua empresa'
        })

@equipe_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    # Filtra os usuários pela empresa do usuário logado
    users = Usuario.query.filter_by(empresa_id=current_user.empresa_id).all()
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
