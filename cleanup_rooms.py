from app import app, db
from models import Sala

def clean_rooms():
    with app.app_context():
        # Busca todas as salas
        salas = Sala.query.all()
        for sala in salas:
            try:
                # Extrai o número da sala após o texto "Sala "
                numero = int(sala.nome.replace("Sala ", ""))
                # Se não estiver entre 18 e 24, deleta
                if not (18 <= numero <= 24):
                    db.session.delete(sala)
            except ValueError:
                # Se o nome não seguir o padrão (ex: "Sala 401"), deleta
                db.session.delete(sala)
        
        db.session.commit()
        print("Limpeza concluída. Restaram apenas as salas de 18 a 24.")

if __name__ == "__main__":
    clean_rooms()
