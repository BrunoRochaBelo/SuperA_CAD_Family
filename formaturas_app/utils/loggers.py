import logging
from flask_login import current_user

# Loggers configurados em setup_loggers()
logger_access = logging.getLogger("access")
logger_crud   = logging.getLogger("crud")
logger_audit  = logging.getLogger("audit")

def _get_tenant_and_user(usuario: str = None):
    """
    Retorna uma tupla (tenant, usuario_str), onde:
      - tenant: current_user.empresa_id (ou 'desconhecido')
      - usuario_str: o email do current_user, ou a string passada em 'usuario', ou 'anonimo'
    """
    if usuario:
        user_str = usuario
        tenant = getattr(current_user, 'empresa_id', 'desconhecido')
    elif current_user and current_user.is_authenticated:
        user_str = current_user.email
        tenant = getattr(current_user, 'empresa_id', 'desconhecido')
    else:
        user_str = 'anonimo'
        tenant = 'desconhecido'
    return tenant, user_str

def log_access(mensagem: str, usuario: str = None):
    """
    Registra eventos de acesso (visualização de páginas, tentativas de login etc).
    Exemplo: log_access("Acessou dashboard")
    """
    tenant, user_str = _get_tenant_and_user(usuario)
    logger_access.info(f"[empresa:{tenant}] {mensagem} | Usuário: {user_str}")

def log_crud(acao: str, entidade: str, usuario: str = None):
    """
    Registra criação, edição ou exclusão de dados.
    Exemplo: log_crud("criou", "empresa X")
    """
    tenant, user_str = _get_tenant_and_user(usuario)
    logger_crud.info(f"[empresa:{tenant}] Usuário: {user_str} {acao} {entidade}")

def log_audit(evento: str, usuario: str = None):
    """
    Registra eventos de segurança/auditoria (falhas, origens bloqueadas etc).
    Exemplo: log_audit("validacao_senha_falhou")
    """
    tenant, user_str = _get_tenant_and_user(usuario)
    logger_audit.warning(f"[empresa:{tenant}] {evento} | Usuário: {user_str}")
