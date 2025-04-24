from functools import wraps
from flask import (
    flash,
    redirect,
    url_for,
    render_template,
    request,
    jsonify,
    current_app,
)
from flask_login import current_user
from formaturas_app.models import Formando

def require_active_assinatura(func):
    """
    Verifica se a empresa do usuário possui assinatura ativa.
    Se não, exibe flash e redireciona para a tela de login.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user and not current_user.empresa.assinatura_valida():
            flash(
                "Assinatura expirada! Regularize o pagamento para acessar o sistema.",
                "danger",
            )
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper

def require_trusted_origin(allowed_hosts=None):
    """
    Protege endpoints AJAX contra chamadas de origens não confiáveis.
    Permite:
      - Requests sem Origin (ex: curl, dev local)
      - Origin contendo "localhost", "127.0.0.1" ou domínios autorizados
    """
    if allowed_hosts is None:
        allowed_hosts = [
            "127.0.0.1",
            "localhost",
            "supera-cad-family.onrender.com",
        ]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            origin = request.headers.get("Origin", "")
            if origin and not any(host in origin for host in allowed_hosts):
                current_app.logger.warning(
                    f"[ORIGIN BLOQUEADA] {origin} tentou acessar {request.path}"
                )
                return jsonify(valid=False), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def exige_turma(active_page, title, message, button_endpoint='turmas.nova_turma'):
    """
    Garante que exista ao menos UMA turma **da empresa logada**.
    Se não houver, renderiza shared/sem_turmas.html passando:
      - active_page: aba ativa
      - fallback_title: título principal da mensagem
      - fallback_message: texto explicativo
      - button_endpoint: endpoint pro botão de criar turma
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # conta só as turmas da empresa do usuário atual
            primeira = (
                Formando.query
                       .filter(Formando.empresa_id == current_user.empresa_id)
                       .with_entities(Formando.turma)
                       .distinct()
                       .first()
            )
            if not primeira:
                return render_template(
                    "shared/sem_turmas.html",
                    active_page=active_page,
                    fallback_title=title,
                    fallback_message=message,
                    button_endpoint=button_endpoint
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
