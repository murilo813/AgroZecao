from flask import Blueprint, render_template, request, redirect, flash, session
from functions import carregar_usuarios

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST', 'GET'])
def login():
    print("Entrou na rota /login")
    if request.method == 'POST':  # Só processa o formulário quando for POST
        nome = request.form.get('username', '').strip()  # Remove espaços em branco
        senha = request.form.get('password', '').strip()  # Remove espaços em branco

        # Carrega os usuários do banco de dados
        usuarios = carregar_usuarios()

        # Verifica se existe um usuário com o nome e senha fornecidos
        usuario_encontrado = next((user for user in usuarios if user[0] == nome and user[1] == senha), None)

        if usuario_encontrado:  # Se o usuário foi encontrado
            session['usuario'] = nome  # Guarda o nome do usuário na sessão
            print(f"Usuário logado: {nome}")
            return redirect('/home')
        else:
            flash('Nome de usuário ou senha incorretos. Por favor, tente novamente.')
            return redirect('/login')

    return render_template('login.html')

@login_bp.route('/logout')
def logout():
    session.clear()  # Limpa os dados da sessão ao fazer logout
    return redirect('/')  # Redireciona para a página de login após logout