from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Usuario, Sala
from app.utils.decorators import admin_required
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_usuarios():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            username = request.form.get('username')
            password = request.form.get('password')
            is_admin = request.form.get('is_admin') == 'true'
            
            if Usuario.query.filter_by(username=username).first():
                flash('Nome de usuário já existe.', 'error')
            else:
                novo_usuario = Usuario(username=username, is_admin=is_admin)
                novo_usuario.set_senha(password)
                db.session.add(novo_usuario)
                db.session.commit()
                flash('Usuário criado com sucesso!', 'success')
                
        elif action == 'delete':
            user_id = request.form.get('user_id')
            usuario = Usuario.query.get(user_id)
            if usuario:
                db.session.delete(usuario)
                db.session.commit()
                flash('Usuário removido com sucesso!', 'success')
                
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@admin_bp.route('/salas', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_salas():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            nome = request.form.get('nome')
            andar = request.form.get('andar')
            
            if Sala.query.filter_by(nome=nome).first():
                flash('Já existe uma sala com este nome.', 'error')
            else:
                nova_sala = Sala(nome=nome, andar=andar)
                db.session.add(nova_sala)
                db.session.commit()
                flash('Sala criada com sucesso!', 'success')
                
        elif action == 'delete':
            sala_id = request.form.get('sala_id')
            sala = Sala.query.get(sala_id)
            if sala:
                db.session.delete(sala)
                db.session.commit()
                flash('Sala removida com sucesso!', 'success')
                
    salas = Sala.query.order_by(Sala.ordem).all()
    return render_template('salas.html', salas=salas)

@admin_bp.route('/salas/reordenar', methods=['POST'])
@login_required
@admin_required
def reordenar_salas():
    order_ids = request.json.get('ordem', [])
    for index, sala_id in enumerate(order_ids):
        sala = Sala.query.get(sala_id)
        if sala:
            sala.ordem = index
    db.session.commit()
    return {'status': 'success'}, 200
