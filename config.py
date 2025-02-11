import os

class Config:
    ENV = 'production'  # Define o ambiente como produção
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')  # Chave secreta
