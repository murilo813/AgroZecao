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
        print(f"{data_hoje}")
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
                    print(f"{data_agendamento}")

                    if data_agendamento == data_hoje:
                        flash(
                            f"{atendimento['nome_cliente']}\n"
                            f"{atendimento['observacao']}\n"
                            f"{data_atendimento}",
                            category='success'
                        )
                    elif data_agendamento < data_hoje:
                        flash(
                            f"{atendimento['nome_cliente']}\n"
                            f"{atendimento['observacao']}\n"
                            f"{data_atendimento}\n"
                            f"Aviso perdido {data_agendamento}",
                            category='warning'
                        )

                    cursor.execute("""
                        UPDATE atendimentos
                        SET data_agendamento = NULL
                        WHERE cpf_cnpj = %s AND data_agendamento = %s
                    """, (atendimento['cpf_cnpj'], data_agendamento))
                    conexao.commit()

        except Exception as e:
            flash(f"Erro ao verificar atendimentos agendados: {e}", category='error')
        finally:
            if 'conexao' in locals():
                conexao.close()

    return render_template('home.html', nomeclatura=nomeclatura)