from flask import Blueprint, render_template, request, redirect, flash, session
from functions import carregar_usuarios

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':  
        nome = request.form.get('username', '').strip()  
        senha = request.form.get('password', '').strip() 

        usuarios = carregar_usuarios()

        usuario_encontrado = next((user for user in usuarios if user[0] == nome and user[1] == senha), None)

        if usuario_encontrado:  
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