# formaturas_app/utils/helpers.py

# Valor padrão caso o campo max_usuarios não esteja definido na empresa
DEFAULT_LIMITE_USUARIOS = 5

def get_limite_empresa(empresa):
    """
    Retorna o limite de usuários da empresa.
    Se o atributo max_usuarios estiver definido (não nulo ou 0), ele é retornado; 
    caso contrário, retorna o valor padrão DEFAULT_LIMITE_USUARIOS.
    """
    return empresa.max_usuarios if empresa.max_usuarios else DEFAULT_LIMITE_USUARIOS
