from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from formaturas_app.models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(nome=nome).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home.index', active_page='home'))
        flash('Login inválido!', 'danger')
    return render_template('auth/login.html', active_page='login')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout efetuado.', 'info')
    return redirect(url_for('auth.login'))
