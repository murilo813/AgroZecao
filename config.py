import os

class Config:
    ENV = 'production' 
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')  
