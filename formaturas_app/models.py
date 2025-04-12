import datetime
import enum
from formaturas_app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

# Enum para definir os papéis dos usuários
class PapelEnum(enum.Enum):
    ADM = "ADM"
    EDITOR = "EDITOR"
    VISUALIZADOR = "VISUALIZADOR"

class Empresa(db.Model):
    """
    Modelo para representar uma empresa cliente.
    Possui um nome único, a data até quando a assinatura está ativa e o limite de usuários permitidos.
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    assinatura_ativa_ate = db.Column(db.Date, nullable=False)
    max_usuarios = db.Column(db.Integer, nullable=False, default=5)  # Limite de usuários com fallback padrão
    usuarios = db.relationship('Usuario', backref='empresa', lazy=True)

    def assinatura_valida(self) -> bool:
        """Retorna True se a assinatura estiver ativa (data maior ou igual à hoje)."""
        return self.assinatura_ativa_ate >= datetime.date.today()

    def __repr__(self):
        return f"<Empresa {self.nome}>"

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Usado para login
    nome = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    foto_perfil = db.Column(db.String(200), nullable=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    # O campo 'papel' é definido como enum para garantir consistência
    papel = db.Column(db.Enum(PapelEnum), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)

    def set_password(self, password: str) -> None:
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.senha_hash, password)
    
    @property
    def papel_str(self) -> str:
        return self.papel.value

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email é obrigatório")
        return email.lower()  # Padroniza o email para lowercase

    def __repr__(self):
        return f"<Usuario {self.email}>"

class Formando(db.Model):
    """
    Modelo para representar um formando.
    Relaciona-se com 'Parente' por meio de um relacionamento em cascade.
    """
    id = db.Column(db.Integer, primary_key=True)
    turma = db.Column(db.String(100), nullable=False)
    aluno = db.Column(db.String(100), nullable=False)
    parentes = db.relationship('Parente', backref='formando', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return f"<Formando {self.aluno} da turma {self.turma}>"

class Parente(db.Model):
    """
    Modelo para representar um parente associado ao formando.
    """
    id = db.Column(db.Integer, primary_key=True)
    formando_id = db.Column(db.Integer, db.ForeignKey('formando.id', ondelete='CASCADE'), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    grau = db.Column(db.String(50), nullable=False)
    telefone = db.Column(db.String(15), nullable=False, default='-')
    data_nascimento = db.Column(db.Date, nullable=True)
    profissao = db.Column(db.String(100), nullable=True)
    comprou_foto = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Parente {self.nome} - {self.grau}>"

    @validates('nome', 'grau', 'cidade')
    def validate_non_empty(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError(f"O campo '{key}' é obrigatório e não pode ser vazio.")
        cleaned = value.strip()
        if key == 'cidade':
            # Padroniza a cidade para evitar variações indesejadas
            cleaned = cleaned.title()
        return cleaned

    @validates('data_nascimento')
    def validate_data_nascimento(self, key: str, value) -> any:
        if not value or value == "":
            return None
        if isinstance(value, str):
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Formato inválido para data_nascimento. Use AAAA-MM-DD.")
        elif not isinstance(value, datetime.date):
            raise ValueError("Formato inválido para data_nascimento.")
        return value

# Adicionando o callback user_loader para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
