from flask import Flask, render_template, request, redirect, url_for, flash, abort
from models import db, Sala, Reserva, Usuario
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import os
import pytz

app = Flask(__name__)

# Configuração de Banco de Dados (PostgreSQL para Cloud, SQLite para Local)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///reservas.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def get_now_br():
    """Retorna o datetime atual no fuso horário de Brasília/Recife (com info de fuso)."""
    return datetime.now(pytz.timezone('America/Recife'))

def get_now_br_naive():
    """Retorna o datetime atual no fuso horário de Brasília/Recife (sem info de fuso, apenas wall-clock)."""
    return get_now_br().replace(tzinfo=None)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso não autorizado.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    with app.app_context():
        db.create_all()
        # Inicializar salas se não existirem (Salas 18 a 24)
        salas_nomes = [f"Sala {i}" for i in range(18, 25)]
        for nome in salas_nomes:
            if not Sala.query.filter_by(nome=nome).first():
                nova_sala = Sala(nome=nome, andar="4º Andar")
                db.session.add(nova_sala)
        
        # Criar usuário admin padrão se não houver usuários
        if not Usuario.query.first():
            admin = Usuario(username="admin", is_admin=True)
            admin.set_senha("admin")
            db.session.add(admin)
        
        db.session.commit()

# Inicializa o banco ao carregar o app
init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_senha(senha):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha inválidos.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    salas = Sala.query.order_by(Sala.ordem).all()
    agora = get_now_br_naive()
    
    status_salas = []
    for sala in salas:
        # Verifica se há reserva acontecendo NESTE MOMENTO
        # inicio <= agora <= fim (comparando naive com naive de Brasília)
        reserva_atual = Reserva.query.filter(
            Reserva.sala_id == sala.id,
            Reserva.inicio <= agora,
            Reserva.fim >= agora
        ).first()
        
        status_salas.append({
            'info': sala,
            'ocupada': reserva_atual is not None,
            'reserva_atual': reserva_atual
        })
    
    return render_template('dashboard.html', status_salas=status_salas)

@app.route('/reservar', methods=['GET', 'POST'])
@login_required
def reservar():
    # Pass sala_id to the template if present in query params
    selected_sala_id = request.args.get('sala_id', type=int)
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
            data_base = datetime.strptime(data_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fim = datetime.strptime(hora_fim_str, '%H:%M').time()

            # Combina data e hora e força o fuso de Recife
            fuso = pytz.timezone('America/Recife')
            inicio_dt = fuso.localize(datetime.combine(data_base, hora_inicio))
            fim_dt = fuso.localize(datetime.combine(data_base, hora_fim))
            
            # Garantir que salvamos no banco sem fuso (naive), mas no horário de Brasília/Recife
            # Assim o valor no banco será ex: 10:25 mesmo que o servidor esteja em UTC.
            inicio_naive = inicio_dt.replace(tzinfo=None)
            fim_naive = fim_dt.replace(tzinfo=None)

            # Lógica para "virada de noite": se fim <= inicio, assume dia seguinte
            if fim_dt <= inicio_dt:
                fim_dt += timedelta(days=1)

            # Validação de sobreposição usando os horários normalizados
            conflito = Reserva.query.filter(
                Reserva.sala_id == sala_id,
                Reserva.inicio < fim_naive,
                Reserva.fim > inicio_naive
            ).first()

            if conflito:
                flash(f'Conflito de horário! Já existe uma reserva de {conflito.inicio.strftime("%d/%m %H:%M")} até {conflito.fim.strftime("%H:%M")}.', 'error')
                return redirect(url_for('reservar'))

            nova_reserva = Reserva(
                sala_id=sala_id,
                user_id=current_user.id,
                assunto=assunto,
                nome_solicitante=nome_solicitante,
                setor=setor,
                telefone=telefone,
                inicio=inicio_naive,
                fim=fim_naive
            )
            db.session.add(nova_reserva)
            db.session.commit()
            flash('Reserva realizada com sucesso!', 'success')
            return redirect(url_for('lista_reservas'))

        except Exception as e:
            flash(f'Erro ao processar reserva: {str(e)}', 'error')
            return redirect(url_for('reservar'))

    return render_template('reservar.html', salas=salas, selected_sala_id=selected_sala_id)

@app.route('/reservas')
@login_required
def lista_reservas():
    # Filtros
    sala_id = request.args.get('sala_id', type=int)
    data_str = request.args.get('data')
    
    query = Reserva.query

    # Regra de visibilidade: Comum vê apenas o dele, Admin vê tudo
    if not current_user.is_admin:
        query = query.filter(Reserva.user_id == current_user.id)

    if sala_id:
        query = query.filter(Reserva.sala_id == sala_id)
    
    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, '%Y-%m-%d').date()
            # Filtra pelo dia inteiro (intervalo de 00:00 a 23:59:59)
            inicio_dia = datetime.combine(data_filtro, datetime.min.time())
            fim_dia = datetime.combine(data_filtro, datetime.max.time())
            query = query.filter(Reserva.inicio >= inicio_dia, Reserva.inicio <= fim_dia)
        except ValueError:
            pass # Ignora data inválida

    # Filtro de Status
    status = request.args.get('status')
    agora = get_now_br_naive()
    
    if status == 'agora':
        query = query.filter(Reserva.inicio <= agora, Reserva.fim >= agora)
    elif status == 'futuro':
        query = query.filter(Reserva.inicio > agora)
    elif status == 'concluido':
        query = query.filter(Reserva.fim < agora)

    # Ordena por data de início
    reservas = query.order_by(Reserva.inicio.desc()).all()
    
    # Dados para o filtro
    salas = Sala.query.order_by(Sala.nome).all()
    agora_exibicao = get_now_br() # Para exibição no template podemos usar com fuso se precisar, mas naive resolve local
    
    return render_template('reservas.html', reservas=reservas, salas=salas, agora=agora)

@app.route('/cancelar/<int:id>')
@login_required
def cancelar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    
    # Validação de permissão: Apenas admin ou dono da reserva
    if not current_user.is_admin and reserva.user_id != current_user.id:
        flash('Você não tem permissão para cancelar esta reserva.', 'error')
        return redirect(url_for('lista_reservas'))

    db.session.delete(reserva)
    db.session.commit()
    flash('Reserva cancelada com sucesso.', 'success')
    return redirect(url_for('lista_reservas'))

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_usuarios():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        is_admin = request.form.get('is_admin') == 'on'
        
        if Usuario.query.filter_by(username=username).first():
            flash('Este usuário já existe.', 'error')
        else:
            novo_usuario = Usuario(username=username, is_admin=is_admin)
            novo_usuario.set_senha(senha)
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('gerenciar_usuarios'))
    
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/excluir/<int:id>')
@login_required
@admin_required
def excluir_usuario(id):
    if Usuario.query.count() <= 1:
        flash('Não é possível excluir o único usuário do sistema.', 'error')
        return redirect(url_for('gerenciar_usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('Você não pode excluir o usuário que está logado atualmente.', 'error')
        return redirect(url_for('gerenciar_usuarios'))

    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso.', 'success')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/salas', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_salas():
    if request.method == 'POST':
        nome = request.form.get('nome')
        andar = request.form.get('andar')
        
        if Sala.query.filter_by(nome=nome).first():
            flash('Já existe uma sala com este nome.', 'error')
        else:
            proxima_ordem = db.session.query(db.func.max(Sala.ordem)).scalar() or 0
            nova_sala = Sala(nome=nome, andar=andar, ordem=proxima_ordem + 1)
            db.session.add(nova_sala)
            db.session.commit()
            flash('Sala criada com sucesso!', 'success')
        return redirect(url_for('gerenciar_salas'))
    
    salas = Sala.query.order_by(Sala.ordem, Sala.nome).all()
    return render_template('salas.html', salas=salas)

@app.route('/salas/reordenar', methods=['POST'])
@login_required
@admin_required
def reordenar_salas():
    try:
        ordem_ids = request.json.get('ordem')
        for index, sala_id in enumerate(ordem_ids):
            sala = Sala.query.get(sala_id)
            if sala:
                sala.ordem = index
        db.session.commit()
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 400

@app.route('/salas/excluir/<int:id>')
@login_required
@admin_required
def excluir_sala(id):
    sala = Sala.query.get_or_404(id)
    # Verificar se há reservas futuras? O cascade no model já lida com exclusão,
    # mas pode ser bom avisar. Por enquanto, a remoção é direta.
    db.session.delete(sala)
    db.session.commit()
    flash('Sala excluída com sucesso.', 'success')
    return redirect(url_for('gerenciar_salas'))

if __name__ == '__main__':
    with app.app_context():
        # Check if DB exists and create if not (init_db calls create_all)
        # Note: If schema changed, restart with deleted DB is needed.
        init_db()
    app.run(debug=True)
