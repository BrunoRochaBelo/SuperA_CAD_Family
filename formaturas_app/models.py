# formaturas_app/models.py

import datetime
import enum
import sqlite3
from formaturas_app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

# Enums --------------------------------------------------

class PapelEnum(enum.Enum):
    ADM = "ADM"
    EDITOR = "EDITOR"
    VISUALIZADOR = "VISUALIZADOR"

class StatusEnum(enum.Enum):
    ATIVA = "Ativa"
    INATIVA = "Inativa"

# Model Empresa ------------------------------------------

class Empresa(db.Model):
    """
    Representa uma empresa (tenant). Ao deletar uma Empresa,
    todos os usuários e formandos vinculados são apagados em cascata.
    """
    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    assinatura_ativa_ate = db.Column(db.Date, nullable=False)
    max_usuarios = db.Column(db.Integer, nullable=False, default=5)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.ATIVA)

    # Relações com cascade total
    usuarios = db.relationship(
        'Usuario',
        backref='empresa',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    formandos = db.relationship(
        'Formando',
        backref='empresa',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def assinatura_valida(self) -> bool:
        """True se assinatura ainda não expirou."""
        return self.assinatura_ativa_ate >= datetime.date.today()

    def __repr__(self):
        return f"<Empresa {self.nome} - {self.status.value}>"

# Model Usuario -----------------------------------------

class Usuario(db.Model, UserMixin):
    """
    Usuário do sistema. Pertence a uma Empresa; se a Empresa for deletada,
    o Usuario também cai (ON DELETE CASCADE).
    """
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    foto_perfil = db.Column(db.String(200), nullable=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    papel = db.Column(db.Enum(PapelEnum), nullable=False)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey('empresa.id', ondelete='CASCADE'),
        nullable=False
    )

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
        return email.lower().strip()

    def __repr__(self):
        return f"<Usuario {self.email}>"

# Model Formando ----------------------------------------

class Formando(db.Model):
    """
    Formando (aluno) vinculado a uma turma e a uma Empresa.
    Deletando o Formando, todos os Parentes dele caem junto.
    """
    __tablename__ = 'formando'

    id = db.Column(db.Integer, primary_key=True)
    turma = db.Column(db.String(100), nullable=False)
    aluno = db.Column(db.String(100), nullable=False)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey('empresa.id', ondelete='CASCADE'),
        nullable=False
    )

    parentes = db.relationship(
        'Parente',
        backref='formando',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Formando {self.aluno} da turma {self.turma}>"

# Model Parente -----------------------------------------

class Parente(db.Model):
    """
    Parente associado a um Formando. Se o Formando for deletado,
    o Parente também é apagado (ON DELETE CASCADE).
    """
    __tablename__ = 'parente'

    id = db.Column(db.Integer, primary_key=True)
    formando_id = db.Column(
        db.Integer,
        db.ForeignKey('formando.id', ondelete='CASCADE'),
        nullable=False
    )
    nome = db.Column(db.String(100), nullable=False)
    grau = db.Column(db.String(50), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(15), nullable=False, default='-')
    data_nascimento = db.Column(db.Date, nullable=True)
    profissao = db.Column(db.String(100), nullable=True)
    comprou_foto = db.Column(db.Boolean, default=False)

    @validates('nome', 'grau', 'cidade')
    def validate_non_empty(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError(f"O campo '{key}' é obrigatório e não pode ser vazio.")
        cleaned = value.strip()
        if key == 'cidade':
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

    def __repr__(self):
        return f"<Parente {self.nome} - {self.grau}>"

# Callback Flask-Login ----------------------------------

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário pro Flask-Login a partir do ID."""
    return Usuario.query.get(int(user_id))
