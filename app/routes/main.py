from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Sala, Reserva
from app.utils.time_utils import get_now_br_naive, get_now_br
from datetime import datetime, timedelta
import pytz
import uuid
import calendar

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    salas = Sala.query.order_by(Sala.ordem).all()
    agora = get_now_br_naive()
    
    status_salas = []
    for sala in salas:
        reserva_atual = Reserva.query.filter(
            Reserva.sala_id == sala.id,
            Reserva.inicio <= agora,
            Reserva.fim >= agora
        ).first()
        
        ocupada = reserva_atual is not None
        status = 'Ocupada' if ocupada else 'Disponível'
            
        status_salas.append({
            'sala': sala,
            'status': status,
            'ocupada': ocupada,
            'reserva': reserva_atual
        })

    return render_template('dashboard.html', status_salas=status_salas, agora=agora)

@main_bp.route('/reservar', methods=['GET', 'POST'])
@login_required
def reservar():
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

            # Recorrência
            tipo_recorrencia = request.form.get('tipo_recorrencia', 'nenhuma')
            qtd_repeticoes = int(request.form.get('qtd_repeticoes', 1)) if tipo_recorrencia != 'nenhuma' else 1
            
            if qtd_repeticoes > 12: qtd_repeticoes = 12

            fuso = pytz.timezone('America/Recife')
            series_id = str(uuid.uuid4()) if tipo_recorrencia != 'nenhuma' else None
            
            reservas_para_criar = []
            conflitos = []

            for i in range(qtd_repeticoes):
                if tipo_recorrencia == 'mensal':
                    new_month = data_base.month + i
                    new_year = data_base.year + (new_month - 1) // 12
                    new_month = (new_month - 1) % 12 + 1
                    last_day = calendar.monthrange(new_year, new_month)[1]
                    new_day = min(data_base.day, last_day)
                    nova_data = datetime(new_year, new_month, new_day).date()
                else:
                    delta_days = 0
                    if tipo_recorrencia == 'semanal': delta_days = i * 7
                    elif tipo_recorrencia == 'quinzenal': delta_days = i * 14
                    nova_data = data_base + timedelta(days=delta_days)
                
                inicio_dt = fuso.localize(datetime.combine(nova_data, hora_inicio))
                fim_dt = fuso.localize(datetime.combine(nova_data, hora_fim))
                
                if fim_dt <= inicio_dt:
                    fim_dt += timedelta(days=1)

                inicio_naive = inicio_dt.replace(tzinfo=None)
                fim_naive = fim_dt.replace(tzinfo=None)

                conflito = Reserva.query.filter(
                    Reserva.sala_id == sala_id,
                    Reserva.inicio < fim_naive,
                    Reserva.fim > inicio_naive
                ).first()

                if conflito:
                    conflitos.append(f"{nova_data.strftime('%d/%m')}")
                else:
                    nova_reserva = Reserva(
                        sala_id=sala_id,
                        user_id=current_user.id,
                        assunto=assunto,
                        nome_solicitante=nome_solicitante,
                        setor=setor,
                        telefone=telefone,
                        inicio=inicio_naive,
                        fim=fim_naive,
                        recorrencia_id=series_id,
                        is_recorrente=(tipo_recorrencia != 'nenhuma')
                    )
                    reservas_para_criar.append(nova_reserva)

            if conflitos:
                if len(reservas_para_criar) == 0:
                    flash(f'Erro: Todos os horários selecionados possuem conflitos: {", ".join(conflitos)}', 'error')
                    return redirect(url_for('main.reservar'))
                else:
                    flash(f'Algumas reservas foram criadas, mas as seguintes datas tiveram conflitos e foram puladas: {", ".join(conflitos)}', 'warning')
            
            for r in reservas_para_criar:
                db.session.add(r)
            
            db.session.commit()
            flash(f'{len(reservas_para_criar)} reserva(s) realizada(s) com sucesso!', 'success')
            return redirect(url_for('main.lista_reservas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar reserva: {str(e)}', 'error')
            return redirect(url_for('main.reservar'))
            
    return render_template('reservar.html', salas=salas, selected_sala_id=selected_sala_id)

@main_bp.route('/reservas')
@login_required
def lista_reservas():
    query = Reserva.query
    
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
        
    sala_id = request.args.get('sala_id')
    if sala_id:
        query = query.filter_by(sala_id=sala_id)
        
    data_filtro = request.args.get('data')
    if data_filtro:
        try:
            data_obj = datetime.strptime(data_filtro, '%Y-%m-%d')
            inicio_dia = data_obj.replace(hour=0, minute=0, second=0)
            fim_dia = data_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Reserva.inicio >= inicio_dia, Reserva.inicio <= fim_dia)
        except:
            pass

    status = request.args.get('status')
    agora = get_now_br_naive()
    
    if status == 'agora':
        query = query.filter(Reserva.inicio <= agora, Reserva.fim >= agora)
    elif status == 'futuro':
        query = query.filter(Reserva.inicio > agora)
    elif status == 'concluido':
        query = query.filter(Reserva.fim < agora)

    reservas = query.order_by(Reserva.inicio.desc()).all()
    salas = Sala.query.order_by(Sala.nome).all()
    agora = get_now_br_naive()
    
    return render_template('reservas.html', reservas=reservas, salas=salas, agora=agora)

@main_bp.route('/cancelar/<int:id>')
@login_required
def cancelar_reserva(id):
    reserva = Reserva.query.get_or_404(id)
    
    if not current_user.is_admin and reserva.user_id != current_user.id:
        flash('Você não tem permissão para cancelar esta reserva.', 'error')
        return redirect(url_for('main.lista_reservas'))

    tipo_cancelamento = request.args.get('tipo', 'unica')
    
    if tipo_cancelamento == 'serie' and reserva.recorrencia_id:
        reservas_serie = Reserva.query.filter_by(recorrencia_id=reserva.recorrencia_id).all()
        contagem = len(reservas_serie)
        for r in reservas_serie:
            db.session.delete(r)
        flash(f'Série de {contagem} reservas cancelada com sucesso.', 'success')
    else:
        db.session.delete(reserva)
        flash('Reserva cancelada com sucesso.', 'success')
    
    db.session.commit()
    return redirect(url_for('main.lista_reservas'))
