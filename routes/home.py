from flask import Blueprint, session, flash, redirect, render_template, request, jsonify
from functions import criar_conexao, obter_notificacoes
from datetime import date
from psycopg2.extras import RealDictCursor

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def home():
    if 'usuario' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect ('/login')

    usuario_logado = session['usuario']

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        query = """
            SELECT nomeclatura
            FROM usuarios
            WHERE nome = %s
        """
        cursor.execute(query, (usuario_logado,))
        resultado = cursor.fetchone()
        nomeclatura = resultado[0] if resultado else 'Usuário'
        session['nomeclatura'] = nomeclatura

    except Exception as e:
        print(f"Erro ao buscar nomeclatura: {e}")
        nomeclatura = 'Usuário'
    finally:
        if conexao:
            conexao.close()

    session['notificacoes'] = obter_notificacoes(usuario_logado)

    return render_template('home.html', nomeclatura=nomeclatura, notificacoes=session['notificacoes'])