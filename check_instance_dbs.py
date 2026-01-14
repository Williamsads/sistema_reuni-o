import sqlite3
import os

# Verifica ambos os bancos na pasta instance
for db_name in ['sistema.db', 'reservas.db']:
    db_path = os.path.join('instance', db_name)
    
    if not os.path.exists(db_path):
        print(f"❌ {db_name} não encontrado")
        continue
        
    print(f"\n{'='*50}")
    print(f"📁 Verificando: {db_path}")
    print('='*50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"Tabelas: {tabelas}")
    
    # Conta registros
    if 'sala' in tabelas:
        cursor.execute("SELECT COUNT(*) FROM sala")
        total_salas = cursor.fetchone()[0]
        print(f"\n🏢 Total de salas: {total_salas}")
        
        if total_salas > 0:
            cursor.execute("SELECT * FROM sala LIMIT 5")
            print("Primeiras salas:")
            for sala in cursor.fetchall():
                print(f"  - {sala}")
    
    if 'usuario' in tabelas:
        cursor.execute("SELECT COUNT(*) FROM usuario")
        print(f"👤 Total de usuários: {cursor.fetchone()[0]}")
    
    if 'reserva' in tabelas:
        cursor.execute("SELECT COUNT(*) FROM reserva")
        print(f"📅 Total de reservas: {cursor.fetchone()[0]}")
    
    conn.close()
