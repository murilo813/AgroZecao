from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from functions import carregar_usuario_por_nome
from werkzeug.security import check_password_hash
from extensions import limiter  

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    if 'usuario' in session:
        return redirect('/home')
    return redirect(url_for('login.login'))

@login_bp.route('/login', methods=['POST', 'GET'])
@limiter.limit("5 per minute")
def login():
    if 'usuario' in session:
        return redirect('/home')

    if request.method == 'POST':
        nome = request.form.get('username', '').strip()
        senha = request.form.get('password', '').strip()
        remember = request.form.get('remember_me')

        usuario = carregar_usuario_por_nome(nome)

        if usuario:
            usuario_id = usuario[0]
            id_empresa = usuario[1]
            senha_hash = usuario[2]

            if check_password_hash(senha_hash, senha):
                session.permanent = bool(remember)
                session['usuario'] = nome
                session['usuario_id'] = usuario_id
                session['id_empresa'] = id_empresa
                return redirect('/home')

        flash('Nome de usuário ou senha incorretos. Por favor, tente novamente.')
        return redirect(url_for('login.login'))

    return render_template('login.html')

# logout
@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))