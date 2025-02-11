from flask import Flask
from config import Config
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)  

def register_blueprints(): 
    from routes.login import login_bp  
    from routes.home import home_bp    
    from routes.gerencia import gerencia_bp  
    from routes.consulta import consulta_bp 
    from routes.estoque import estoque_bp
    from routes.comercial import comercial_bp


    app.register_blueprint(login_bp) 
    app.register_blueprint(home_bp)  
    app.register_blueprint(gerencia_bp)
    app.register_blueprint(consulta_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(comercial_bp)

register_blueprints()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)