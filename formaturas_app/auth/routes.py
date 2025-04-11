from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from formaturas_app.models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Realiza o login do usuário utilizando o email.
    Valida também se a assinatura da empresa está ativa antes de permitir o acesso.
    """
    if request.method == 'POST':
        email = request.form.get("email")
        senha = request.form.get("senha")
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_password(senha):
            if not usuario.empresa.assinatura_valida():
                flash("Assinatura expirada! Regularize seu pagamento para acessar o sistema.", "danger")
                return redirect(url_for("auth.login"))
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("home.index", active_page="home"))
        flash("Login inválido! Verifique seu email e senha.", "danger")
    return render_template("auth/login.html", active_page="login")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout efetuado.", "info")
    return redirect(url_for("auth.login"))
