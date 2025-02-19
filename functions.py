import psycopg2
import os

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