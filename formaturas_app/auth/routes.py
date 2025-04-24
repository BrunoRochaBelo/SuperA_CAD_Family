from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from formaturas_app.models import Usuario, StatusEnum
from formaturas_app.utils.loggers import log_access

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    email_valor = ""
    if request.method == 'POST':
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        email_valor = email

        # traz usuário (se existir)
        usuario = Usuario.query.filter_by(email=email).first()

        # Checa se o usuário EXISTE e se a empresa NÃO foi deletada
        if not usuario or not usuario.empresa:
            log_access(f"Tentativa de login com email inexistente ou sem empresa: {email}")
            flash("Email não encontrado. Verifique o endereço digitado.", "danger")
            return render_template(
                "auth/login.html", active_page="login", email_valor=email_valor
            )

        # Valida senha normalmente
        if not usuario.check_password(senha):
            log_access(f"Senha incorreta para o email: {email}")
            flash("Senha incorreta. Tente novamente.", "danger")
            return render_template(
                "auth/login.html", active_page="login", email_valor=email_valor
            )

        # Agora a empresa existe de verdade, posso chamar assinatura_valida()
        if not usuario.empresa.assinatura_valida():
            log_access("Login bloqueado por assinatura expirada")
            flash(
                "Assinatura expirada! Regularize seu pagamento para acessar o sistema.",
                "danger",
            )
            return render_template(
                "auth/login.html", active_page="login", email_valor=email_valor
            )

        if usuario.empresa.status != StatusEnum.ATIVA:
            log_access("Login bloqueado - empresa inativa")
            flash(
                "Sua empresa está inativa. Entre em contato com o administrador do sistema.",
                "danger",
            )
            return render_template(
                "auth/login.html", active_page="login", email_valor=email_valor
            )

        # Tudo certo, loga o usuário
        login_user(usuario)
        log_access("Login realizado com sucesso")
        flash("Login realizado com sucesso!", "success")

        if usuario.email.lower() == "adminbruno@diretiva.com":
            return redirect(url_for("empresa.index"))
        return redirect(url_for("home.index", active_page="home"))

    return render_template(
        "auth/login.html", active_page="login", email_valor=email_valor
    )


@auth_bp.route("/logout")
@login_required
def logout():
    log_access("Logout efetuado")
    logout_user()
    flash("Logout efetuado.", "info")
    return redirect(url_for("auth.login"))
