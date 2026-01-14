"""
Script para copiar dados do banco antigo para o novo banco reorganizado.
"""
from app import create_app, db
from app.models import Usuario, Sala, Reserva
from sqlalchemy import create_engine, text
import os

# Cria a aplicação
app = create_app()

# Caminho do banco antigo (na raiz do projeto)
OLD_DB_PATH = os.path.join(os.path.dirname(__file__), 'sistema.db')

if not os.path.exists(OLD_DB_PATH):
    print(f"❌ Banco antigo não encontrado em: {OLD_DB_PATH}")
    exit(1)

print(f"✅ Banco antigo encontrado: {OLD_DB_PATH}")

# Engine para o banco antigo
old_engine = create_engine(f'sqlite:///{OLD_DB_PATH}')

with app.app_context():
    print("\n🔄 Iniciando migração de dados...\n")
    
    # 1. Migrar Usuários
    print("📋 Migrando usuários...")
    with old_engine.connect() as old_conn:
        usuarios_antigos = old_conn.execute(text("SELECT * FROM usuario")).fetchall()
        
        for user_row in usuarios_antigos:
            # Verifica se já existe
            if not Usuario.query.filter_by(username=user_row[1]).first():
                novo_usuario = Usuario(
                    id=user_row[0],
                    username=user_row[1],
                    senha_hash=user_row[2],
                    is_admin=bool(user_row[3])
                )
                db.session.add(novo_usuario)
        
        db.session.commit()
        print(f"   ✅ {len(usuarios_antigos)} usuários migrados")
    
    # 2. Migrar Salas
    print("🏢 Migrando salas...")
    with old_engine.connect() as old_conn:
        salas_antigas = old_conn.execute(text("SELECT * FROM sala")).fetchall()
        
        for sala_row in salas_antigas:
            if not Sala.query.filter_by(nome=sala_row[1]).first():
                nova_sala = Sala(
                    id=sala_row[0],
                    nome=sala_row[1],
                    andar=sala_row[2] if len(sala_row) > 2 else "4º Andar",
                    ordem=sala_row[3] if len(sala_row) > 3 else 0
                )
                db.session.add(nova_sala)
        
        db.session.commit()
        print(f"   ✅ {len(salas_antigas)} salas migradas")
    
    # 3. Migrar Reservas
    print("📅 Migrando reservas...")
    with old_engine.connect() as old_conn:
        # Verifica se as colunas de recorrência existem
        try:
            reservas_antigas = old_conn.execute(text(
                "SELECT id, sala_id, user_id, assunto, nome_solicitante, setor, telefone, inicio, fim, data_criacao, recorrencia_id, is_recorrente FROM reserva"
            )).fetchall()
            has_recurrence = True
        except:
            reservas_antigas = old_conn.execute(text(
                "SELECT id, sala_id, user_id, assunto, nome_solicitante, setor, telefone, inicio, fim, data_criacao FROM reserva"
            )).fetchall()
            has_recurrence = False
        
        for reserva_row in reservas_antigas:
            if not Reserva.query.get(reserva_row[0]):
                nova_reserva = Reserva(
                    id=reserva_row[0],
                    sala_id=reserva_row[1],
                    user_id=reserva_row[2],
                    assunto=reserva_row[3],
                    nome_solicitante=reserva_row[4],
                    setor=reserva_row[5],
                    telefone=reserva_row[6],
                    inicio=reserva_row[7],
                    fim=reserva_row[8],
                    data_criacao=reserva_row[9],
                    recorrencia_id=reserva_row[10] if has_recurrence and len(reserva_row) > 10 else None,
                    is_recorrente=reserva_row[11] if has_recurrence and len(reserva_row) > 11 else False
                )
                db.session.add(nova_reserva)
        
        db.session.commit()
        print(f"   ✅ {len(reservas_antigas)} reservas migradas")
    
    print("\n🎉 Migração concluída com sucesso!")
    print(f"📊 Resumo:")
    print(f"   - Usuários: {Usuario.query.count()}")
    print(f"   - Salas: {Sala.query.count()}")
    print(f"   - Reservas: {Reserva.query.count()}")
