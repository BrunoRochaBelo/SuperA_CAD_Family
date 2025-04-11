import datetime
import enum
from formaturas_app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

# Define o Enum para os papéis dos usuários
class PapelEnum(enum.Enum):
    ADM = "ADM"
    EDITOR = "EDITOR"
    VISUALIZADOR = "VISUALIZADOR"

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    papel = db.Column(db.Enum(PapelEnum), nullable=False)

    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)
    
    @property
    def papel_str(self):
        return self.papel.value

    def __repr__(self):
        return f"<Usuario {self.nome}>"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Formando(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma = db.Column(db.String(100), nullable=False)
    aluno = db.Column(db.String(100), nullable=False)
    # Importante: relacionamento em cascade para garantir exclusão de Parentes órfãos
    parentes = db.relationship('Parente', backref='formando', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return f"<Formando {self.aluno} da turma {self.turma}>"

class Parente(db.Model):
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
    def validate_non_empty(self, key, value):
        if not value or not value.strip():
            raise ValueError(f"O campo '{key}' é obrigatório e não pode ser vazio.")
        cleaned = value.strip()
        if key == 'cidade':
            # Padroniza a cidade para evitar variações indesejadas
            cleaned = cleaned.title()
        return cleaned

    @validates('data_nascimento')
    def validate_data_nascimento(self, key, value):
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
