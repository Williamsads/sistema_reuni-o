import os
import sqlite3
from sqlalchemy import create_engine, text

# URL do seu banco na nuvem
CLOUD_DB_URL = "postgresql://db_reunioes_user:2sBCKCHUjKBb061BcrpeIFicQKYHMa8T@dpg-d5j9nkf5r7bs73dtrut0-a.virginia-postgres.render.com/db_reunioes"
LOCAL_DB_PATH = "instance/reservas.db"

def migrate():
    if not os.path.exists(LOCAL_DB_PATH):
        print("Arquivo local não encontrado!")
        return

    print("Conectando aos bancos...")
    local_conn = sqlite3.connect(LOCAL_DB_PATH)
    local_cursor = local_conn.cursor()
    
    # Engine do PostgreSQL
    cloud_engine = create_engine(CLOUD_DB_URL)

    try:
        with cloud_engine.begin() as cloud_conn:
            print("Criando tabelas na nuvem (se não existirem)...")
            cloud_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sala (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(50) UNIQUE NOT NULL,
                    andar VARCHAR(20)
                );
                CREATE TABLE IF NOT EXISTS reserva (
                    id SERIAL PRIMARY KEY,
                    sala_id INTEGER NOT NULL REFERENCES sala(id),
                    assunto VARCHAR(100) NOT NULL,
                    nome_solicitante VARCHAR(100) NOT NULL,
                    setor VARCHAR(100) NOT NULL,
                    telefone VARCHAR(20) NOT NULL,
                    data DATE NOT NULL,
                    hora_inicio TIME NOT NULL,
                    hora_fim TIME NOT NULL,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            print("Limpando tabelas na nuvem para migração limpa...")
            cloud_conn.execute(text("TRUNCATE TABLE reserva, sala RESTART IDENTITY CASCADE"))

            # 1. Migrar Salas
            print("Migrando Salas...")
            local_cursor.execute("SELECT id, nome, andar FROM sala")
            salas = local_cursor.fetchall()
            for sala in salas:
                cloud_conn.execute(
                    text("INSERT INTO sala (id, nome, andar) VALUES (:id, :nome, :andar)"),
                    {"id": sala[0], "nome": sala[1], "andar": sala[2]}
                )
            
            # 2. Migrar Reservas
            print("Migrando Reservas...")
            local_cursor.execute("SELECT id, sala_id, assunto, nome_solicitante, setor, telefone, data, hora_inicio, hora_fim, data_criacao FROM reserva")
            reservas = local_cursor.fetchall()
            for r in reservas:
                cloud_conn.execute(
                    text("""INSERT INTO reserva (id, sala_id, assunto, nome_solicitante, setor, telefone, data, hora_inicio, hora_fim, data_criacao) 
                         VALUES (:id, :sala_id, :assunto, :nome, :setor, :tel, :data, :h_in, :h_fim, :dt_c)"""),
                    {
                        "id": r[0], "sala_id": r[1], "assunto": r[2], "nome": r[3], 
                        "setor": r[4], "tel": r[5], "data": r[6], "h_in": r[7], 
                        "h_fim": r[8], "dt_c": r[9]
                    }
                )
            
            print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("Todos os seus dados locais agora estão seguros no Render.")

    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
    finally:
        local_conn.close()

if __name__ == "__main__":
    migrate()
