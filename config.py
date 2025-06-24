import os

class Config:
    ENV = 'production' 
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')  

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'