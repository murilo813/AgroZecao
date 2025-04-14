import psycopg2
from flask import g
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

def carregar_usuario_por_nome(nome):
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT senha FROM usuarios WHERE nome = %s", (nome,))
        usuario = cursor.fetchone()

        return usuario[0] if usuario else None  
    except Exception as e:
        print(f"Erro ao carregar usuário: {e}")
        return None

def carregar_atendimentos(cpf_cliente, cpfs_relacionados):
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        query_atendimentos = """
            SELECT a.nome_cliente, a.cpf_cnpj, a.data_atendimento, a.observacao, 
                   u.nomeclatura  
            FROM atendimentos a
            LEFT JOIN usuarios u ON a.usuario = u.nome 
            WHERE a.cpf_cnpj = %s OR a.cpf_cnpj = ANY(%s)
            ORDER BY a.data_atendimento ASC
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
            SELECT nome_cliente, anotacao, data_agendamento, data, criador, id_not, cpf_cnpj
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
                atendimento['cpf_cnpj']
            ]

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
            print(f"🔍 Criador: {noti['criador']}, Anotação: {noti['anotacao']}, ID_NOT: {noti['id_not']}")
            notificacoes.append([
                F"De: {noti['criador']}",  
                noti['anotacao'],
                "",
                noti['id_not']
            ])

    except Exception as e:
        print(f"Erro ao buscar notificações: {e}")
    finally:
        if 'conexao' in locals():
            conexao.close()

    return notificacoes