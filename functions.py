import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import date

def criar_conexao():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def carregar_usuarios():
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, senha FROM usuarios")
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
        return []

def carregar_atendimentos(cpf_cliente, cpfs_relacionados):
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        query_atendimentos = """
            SELECT nome_cliente, cpf_cnpj, data_atendimento, observacao, usuario
            FROM atendimentos
            WHERE cpf_cnpj = %s OR cpf_cnpj = ANY(%s)
            ORDER BY data_atendimento ASC
        """
        cursor.execute(query_atendimentos, (cpf_cliente, cpfs_relacionados))
        atendimentos = cursor.fetchall()

        atendimentos_dict = [
            {
                'nome_cliente': atendimento[0],
                'cpf_cnpj': atendimento[1],
                'data_atendimento': atendimento[2].strftime('%d/%m/%Y'), 
                'observacao': atendimento[3],
                'usuario': atendimento[4],
            }
            for atendimento in atendimentos
        ]

        return atendimentos_dict
    except Exception as e:
        print(f"Erro ao carregar atendimentos: {e}")
        return []

def obter_notificacoes(usuario):
    notificacoes = []
    data_hoje = date.today()

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor(cursor_factory=RealDictCursor)

        # atendimentos
        cursor.execute("""
            SELECT nome_cliente, anotacao, data_agendamento, data, criador, id_not
            FROM not_gerencia
            WHERE criador = %s AND data_agendamento <= %s AND estado = 'ativa'
        """, (usuario, data_hoje))
        atendimentos = cursor.fetchall()

        for atendimento in atendimentos:
            data_atendimento = atendimento['data']
            data_agendamento = atendimento['data_agendamento']

            notificacao = [
                atendimento['nome_cliente'],
                atendimento['anotacao'],
                data_atendimento.strftime('%d/%m/%Y'),
            ]
            if data_agendamento < data_hoje:
                notificacao.append(f"Aviso perdido {data_agendamento.strftime('%d/%m/%Y')}")

            notificacao.append(atendimento['id_not'])  
            notificacoes.append(notificacao)

        # not gerencia
        cursor.execute("""
            SELECT criador, anotacao, id_not
            FROM not_gerencia
            WHERE usuario = %s AND estado = 'ativa'
        """, (usuario,))
        novas_notificacoes = cursor.fetchall()

        for noti in novas_notificacoes:
            print(f"🔍 Criador: {noti['criador']}, Anotação: {noti['anotacao']}, ID_NOT: {noti['id_not']}")  # 🟥 Debug
            notificacoes.append([
                F"De: {noti['criador']}",  
                noti['anotacao'],
                noti['id_not']
            ])

    except Exception as e:
        print(f"Erro ao buscar notificações: {e}")
    finally:
        if 'conexao' in locals():
            conexao.close()

    return notificacoes