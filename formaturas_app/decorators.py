from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def require_active_assinatura(func):
    """
    Decorador que verifica se a empresa do usuário possui a assinatura ativa.
    Se não estiver ativa, exibe uma mensagem e redireciona para a tela de login.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user and not current_user.empresa.assinatura_valida():
            flash("Assinatura expirada! Regularize o pagamento para acessar o sistema.", "danger")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper
