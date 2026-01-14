from app import create_app, db
from sqlalchemy import text

app = create_app()
from sqlalchemy import text

def patch_database():
    with app.app_context():
        # Verifica se estamos usando SQLite ou PostgreSQL
        engine = db.engine
        
        print(f"Detectado banco de dados: {engine.url}")
        
        with engine.connect() as conn:
            # Tenta adicionar as colunas uma por uma
            try:
                conn.execute(text("ALTER TABLE reserva ADD COLUMN recorrencia_id VARCHAR(50)"))
                conn.commit()
                print("Coluna 'recorrencia_id' adicionada com sucesso.")
            except Exception as e:
                print(f"Aviso ao adicionar 'recorrencia_id': {e}")

            try:
                conn.execute(text("ALTER TABLE reserva ADD COLUMN is_recorrente BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Coluna 'is_recorrente' adicionada com sucesso.")
            except Exception as e:
                print(f"Aviso ao adicionar 'is_recorrente': {e}")
                
        print("Migração concluída!")

if __name__ == "__main__":
    patch_database()
