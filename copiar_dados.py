"""
Copia dados de reservas.db para sistema.db
"""
import sqlite3
import os

origem = 'instance/reservas.db'
destino = 'instance/sistema.db'

print(f"📦 Copiando dados de {origem} para {destino}...")

# Conecta aos dois bancos
conn_origem = sqlite3.connect(origem)
conn_destino = sqlite3.connect(destino)

cursor_origem = conn_origem.cursor()
cursor_destino = conn_destino.cursor()

# 1. Copiar Usuários
print("\n👤 Copiando usuários...")
cursor_origem.execute("SELECT * FROM usuario")
usuarios = cursor_origem.fetchall()

for user in usuarios:
    try:
        cursor_destino.execute(
            "INSERT OR IGNORE INTO usuario (id, username, senha_hash, is_admin) VALUES (?, ?, ?, ?)",
            user
        )
    except Exception as e:
        print(f"  ⚠️  Erro ao copiar usuário {user[1]}: {e}")

conn_destino.commit()
print(f"  ✅ {len(usuarios)} usuários processados")

# 2. Copiar Salas
print("\n🏢 Copiando salas...")
cursor_origem.execute("SELECT * FROM sala")
salas = cursor_origem.fetchall()

for sala in salas:
    try:
        cursor_destino.execute(
            "INSERT OR IGNORE INTO sala (id, nome, andar, ordem) VALUES (?, ?, ?, ?)",
            sala
        )
    except Exception as e:
        print(f"  ⚠️  Erro ao copiar sala {sala[1]}: {e}")

conn_destino.commit()
print(f"  ✅ {len(salas)} salas processadas")

# 3. Copiar Reservas (se houver)
print("\n📅 Copiando reservas...")
cursor_origem.execute("SELECT * FROM reserva")
reservas = cursor_origem.fetchall()

for reserva in reservas:
    try:
        # Verifica quantas colunas tem
        if len(reserva) == 10:  # Sem recorrência
            cursor_destino.execute(
                "INSERT OR IGNORE INTO reserva (id, sala_id, user_id, assunto, nome_solicitante, setor, telefone, inicio, fim, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                reserva
            )
        else:  # Com recorrência
            cursor_destino.execute(
                "INSERT OR IGNORE INTO reserva (id, sala_id, user_id, assunto, nome_solicitante, setor, telefone, inicio, fim, data_criacao, recorrencia_id, is_recorrente) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                reserva
            )
    except Exception as e:
        print(f"  ⚠️  Erro ao copiar reserva: {e}")

conn_destino.commit()
print(f"  ✅ {len(reservas)} reservas processadas")

# Fecha conexões
conn_origem.close()
conn_destino.close()

print("\n🎉 Migração concluída!")

# Verifica resultado
conn_check = sqlite3.connect(destino)
cursor_check = conn_check.cursor()

cursor_check.execute("SELECT COUNT(*) FROM sala")
print(f"\n📊 Resultado final em {destino}:")
print(f"  - Salas: {cursor_check.fetchone()[0]}")

cursor_check.execute("SELECT COUNT(*) FROM usuario")
print(f"  - Usuários: {cursor_check.fetchone()[0]}")

cursor_check.execute("SELECT COUNT(*) FROM reserva")
print(f"  - Reservas: {cursor_check.fetchone()[0]}")

conn_check.close()
