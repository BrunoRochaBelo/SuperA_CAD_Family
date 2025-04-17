from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from flask import request, jsonify, current_app

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

def require_trusted_origin(allowed_hosts=None):
    """
    Decorador para proteger endpoints AJAX sensíveis contra chamadas de origens não confiáveis.
    Permite:
      - Requisições sem Origin (ex: curl, dev local)
      - Origem contendo "localhost", "127.0.0.1" ou domínios autorizados
    """
    if allowed_hosts is None:
        allowed_hosts = [
            "127.0.0.1",
            "localhost",
            "supera-cad-family.onrender.com",  # domínio de produção
        ]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            origin = request.headers.get("Origin", "")
            if origin and not any(host in origin for host in allowed_hosts):
                current_app.logger.warning(f"[ORIGIN BLOQUEADA] {origin} tentou acessar {request.path}")
                return jsonify(valid=False), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

    """
    Decorador para proteger endpoints AJAX sensíveis contra chamadas de origens não confiáveis.
    Permite:
      - Requisições sem Origin (ex: curl, dev local)
      - Origem contendo "localhost", "127.0.0.1" ou domínios autorizados
    """
    if allowed_hosts is None:
        allowed_hosts = ["127.0.0.1", "localhost", "seusite.com"]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            origin = request.headers.get("Origin", "")
            if origin and not any(host in origin for host in allowed_hosts):
                current_app.logger.warning(f"[ORIGIN BLOQUEADA] {origin} tentou acessar {request.path}")
                return jsonify(valid=False), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator