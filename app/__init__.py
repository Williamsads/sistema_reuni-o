from flask import Flask
from flask_login import LoginManager
from app.models import db, Usuario
from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.admin import admin_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configuração
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
    
    # Configuração do Banco de Dados
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///sistema.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicialização das extensões
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
        
    # Registro dos Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        # Admin padrão
        if not Usuario.query.filter_by(username='admin').first():
            print("Criando usuário admin padrão...")
            admin = Usuario(username='admin', is_admin=True)
            admin.set_senha('admin123')
            db.session.add(admin)
            db.session.commit()
            
    return app

app = create_app()
