from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

db = SQLAlchemy()

def get_now_br():
    """Retorna o datetime atual no fuso horário de Brasília/Recife (com info de fuso)."""
    return datetime.now(pytz.timezone('America/Recife'))

def get_now_br_naive():
    """Retorna o datetime atual no fuso horário de Brasília/Recife (apenas wall-clock)."""
    return get_now_br().replace(tzinfo=None)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    andar = db.Column(db.String(20), default="4º Andar")
    ordem = db.Column(db.Integer, default=0)

    reservas = db.relationship('Reserva', backref='sala', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Sala {self.nome}>'

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    assunto = db.Column(db.String(100), nullable=False)
    nome_solicitante = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    data_criacao = db.Column(db.DateTime, default=get_now_br_naive)
    
    # Campos para Recorrência
    recorrencia_id = db.Column(db.String(50), nullable=True) # UUID para agrupar séries
    is_recorrente = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Reserva {self.assunto} em {self.inicio}>'
