import sqlite3

conn = sqlite3.connect('sistema.db')
cursor = conn.cursor()

# Verifica tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = [row[0] for row in cursor.fetchall()]
print("Tabelas no banco antigo:", tabelas)

# Conta salas
if 'sala' in tabelas:
    cursor.execute("SELECT COUNT(*) FROM sala")
    print("Total de salas:", cursor.fetchone()[0])
    
    cursor.execute("SELECT * FROM sala")
    salas = cursor.fetchall()
    print("\nSalas encontradas:")
    for sala in salas:
        print(f"  - {sala}")

conn.close()
