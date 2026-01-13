from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Sala, Reserva
from datetime import datetime
from sqlalchemy import or_, and_
import os

app = Flask(__name__)

# Configuração de Banco de Dados (PostgreSQL para Cloud, SQLite para Local)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///reservas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')

db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        # Inicializar salas se não existirem (Salas 18 a 24)
        salas_nomes = [f"Sala {i}" for i in range(18, 25)]
        for nome in salas_nomes:
            if not Sala.query.filter_by(nome=nome).first():
                nova_sala = Sala(nome=nome, andar="4º Andar")
                db.session.add(nova_sala)
        db.session.commit()

# Inicializa o banco ao carregar o app
init_db()

@app.route('/')
def dashboard():
    salas = Sala.query.all()
    hoje = datetime.now().date()
    # Adicionar status simplificado para o dashboard (se está ocupada agora)
    agora = datetime.now().time()
    
    status_salas = []
    for sala in salas:
        reserva_atual = Reserva.query.filter(
            Reserva.sala_id == sala.id,
            Reserva.data == hoje,
            Reserva.hora_inicio <= agora,
            Reserva.hora_fim >= agora
        ).first()
        
        status_salas.append({
            'info': sala,
            'ocupada': reserva_atual is not None,
            'reserva_atual': reserva_atual
        })
    
    return render_template('dashboard.html', status_salas=status_salas)

@app.route('/reservar', methods=['GET', 'POST'])
def reservar():
    salas = Sala.query.all()
    if request.method == 'POST':
        sala_id = request.form.get('sala_id')
        assunto = request.form.get('assunto')
        nome_solicitante = request.form.get('nome_solicitante')
        setor = request.form.get('setor')
        telefone = request.form.get('telefone')
        data_str = request.form.get('data')
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fim_str = request.form.get('hora_fim')

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time()

            if hora_inicio >= hora_fim:
                flash('A hora de início deve ser anterior à hora de término.', 'error')
                return redirect(url_for('reservar'))

            # Validação de sobreposição
            conflito = Reserva.query.filter(
                Reserva.sala_id == sala_id,
                Reserva.data == data,
                or_(
                    and_(Reserva.hora_inicio <= hora_inicio, Reserva.hora_fim > hora_inicio),
                    and_(Reserva.hora_inicio < hora_fim, Reserva.hora_fim >= hora_fim),
                    and_(Reserva.hora_inicio >= hora_inicio, Reserva.hora_fim <= hora_fim)
                )
            ).first()

            if conflito:
                flash(f'Já existe uma reserva para esta sala neste horário ({conflito.hora_inicio.strftime("%H:%M")} - {conflito.hora_fim.strftime("%H:%M")}).', 'error')
                return redirect(url_for('reservar'))

            nova_reserva = Reserva(
                sala_id=sala_id,
                assunto=assunto,
                nome_solicitante=nome_solicitante,
                setor=setor,
                telefone=telefone,
                data=data,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim
            )
            db.session.add(nova_reserva)
            db.session.commit()
            flash('Reserva realizada com sucesso!', 'success')
            return redirect(url_for('lista_reservas'))

        except Exception as e:
            flash(f'Erro ao processar reserva: {str(e)}', 'error')
            return redirect(url_for('reservar'))

    return render_template('reservar.html', salas=salas)

@app.route('/reservas')
def lista_reservas():
    reservas = Reserva.query.order_by(Reserva.data.desc(), Reserva.hora_inicio.asc()).all()
    return render_template('reservas.html', reservas=reservas)

@app.route('/cancelar/<int:id>')
def cancelar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    db.session.delete(reserva)
    db.session.commit()
    flash('Reserva cancelada com sucesso.', 'success')
    return redirect(url_for('lista_reservas'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
