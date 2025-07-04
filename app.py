from flask import Flask
from config import Config
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)  
app.permanent_session_lifetime = timedelta(days=7)

def register_blueprints(): 
    from routes.login import login_bp  
    from routes.home import home_bp    
    from routes.gerencia import gerencia_bp  
    from routes.consulta import consulta_bp 
    from routes.estoque import estoque_bp
    from routes.gastos import gastos_bp
    from routes.addorcamento import addorcamento_bp
    from routes.base import base_bp


    app.register_blueprint(login_bp) 
    app.register_blueprint(home_bp)  
    app.register_blueprint(gerencia_bp)
    app.register_blueprint(consulta_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(gastos_bp)
    app.register_blueprint(addorcamento_bp)
    app.register_blueprint(base_bp)

register_blueprints()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)