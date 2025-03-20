from flask import Blueprint, render_template, request, redirect, flash, session
from functions import carregar_usuario_por_nome
from werkzeug.security import check_password_hash

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':  
        nome = request.form.get('username', '').strip()  
        senha = request.form.get('password', '').strip() 

        senha_hash = carregar_usuario_por_nome(nome)

        if senha_hash and check_password_hash(senha_hash, senha):  
            session['usuario'] = nome 
            return redirect('/home')
        else:
            flash('Nome de usuário ou senha incorretos. Por favor, tente novamente.')
            return redirect('/login')

    return render_template('login.html')

@login_bp.route('/logout')
def logout():
    session.clear()  
    return redirect('/')  