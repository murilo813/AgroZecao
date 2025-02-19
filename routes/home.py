from flask import Blueprint, session, flash, redirect, render_template, request
from functions import criar_conexao
from datetime import date
from psycopg2.extras import RealDictCursor

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def home():
    if 'usuario' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect ('/login')

    usuario_logado = session['usuario']
    notificacoes = []

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

    if request.method == 'GET':
        data_hoje = date.today().strftime('%d/%m/%Y')
        try:
            conexao = criar_conexao()
            cursor = conexao.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT nome_cliente, cpf_cnpj, data_agendamento, data_atendimento, observacao, usuario
                FROM atendimentos
                WHERE usuario = %s AND data_agendamento <= %s
            """, (session['usuario'], data_hoje))
            atendimentos_filtrados = cursor.fetchall()

            if atendimentos_filtrados:
                for atendimento in atendimentos_filtrados:
                    data_atendimento = atendimento['data_atendimento'].strftime('%d/%m/%Y') if atendimento['data_atendimento'] else None
                    data_agendamento = atendimento['data_agendamento'].strftime('%d/%m/%Y')

                    if data_agendamento == data_hoje:
                        notificacoes.append([
                            atendimento['nome_cliente'],
                            atendimento['observacao'],
                            data_atendimento
                        ])
                    elif data_agendamento < data_hoje:
                        notificacoes.append([
                            atendimento['nome_cliente'],
                            atendimento['observacao'],
                            data_atendimento,
                            f"Aviso perdido {data_agendamento}"
                        ])

        except Exception as e:
            flash(f"Erro ao verificar atendimentos agendados: {e}", category='error')
        finally:
            if 'conexao' in locals():
                conexao.close()

        session['notificacoes'] = notificacoes


    return render_template('home.html', nomeclatura=nomeclatura, notificacoes=notificacoes)