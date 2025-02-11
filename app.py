from flask import Flask
from config import Config
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)  # Carrega as configurações do arquivo config.py

def register_blueprints():
    from routes.login import login_bp  # Agora importa diretamente o objeto login_bp
    from routes.home import home_bp    # Agora importa diretamente o objeto home_bp
    from routes.gerencia import gerencia_bp  # Agora importa diretamente o objeto gerencia_bp
    from routes.consulta import consulta_bp  # Agora importa diretamente o objeto consulta_bp

    app.register_blueprint(login_bp) 
    app.register_blueprint(home_bp)  
    app.register_blueprint(gerencia_bp)
    app.register_blueprint(consulta_bp)

register_blueprints()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)