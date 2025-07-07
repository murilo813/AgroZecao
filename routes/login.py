from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from functions import carregar_usuario_por_nome
from werkzeug.security import check_password_hash
from extensions import limiter  

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    if 'usuario' in session:
        return redirect('/home')
    return render_template('login.html')

@login_bp.route('/login', methods=['POST', 'GET'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        nome = request.form.get('username', '').strip()
        senha = request.form.get('password', '').strip()
        remember = request.form.get('remember_me')

        senha_hash = carregar_usuario_por_nome(nome)

        if senha_hash and check_password_hash(senha_hash, senha):
            session.permanent = True if remember else False
            session['usuario'] = nome
            return redirect('/home')
        else:
            flash('Nome de usuário ou senha incorretos. Por favor, tente novamente.')
            return redirect('/login')

    return render_template('login.html')

@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.index'))