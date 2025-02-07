from flask import Flask, render_template, request, redirect, flash, session, jsonify, send_from_directory
import os
import psycopg2
from psycopg2.extras import RealDictCursor  
from datetime import date, datetime
import locale
import unicodedata

app = Flask(__name__)
app.config['ENV'] = 'production'  # Define o ambiente como produção
app.jinja_env.add_extension('jinja2.ext.do')  # Adicionando a extensão do Jinja
app.secret_key = os.getenv('FLASK_SECRET_KEY')
data_hoje = date.today()

print(data_hoje)

def criar_conexao():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    print(f"Conexão bem-sucedida com o banco de dados: {os.getenv('DB_NAME')}")

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

        # Filtra os atendimentos por CPF do cliente e relacionados
        query_atendimentos = """
            SELECT nome_cliente, cpf_cnpj, data_atendimento, observacao, usuario
            FROM atendimentos
            WHERE cpf_cnpj = %s OR cpf_cnpj = ANY(%s)
        """
        cursor.execute(query_atendimentos, (cpf_cliente, cpfs_relacionados))
        atendimentos = cursor.fetchall()

        # Converte os resultados em uma lista de dicionários
        atendimentos_dict = [
            {
                'nome_cliente': atendimento[0],
                'cpf_cnpj': atendimento[1],
                'data_atendimento': atendimento[2].strftime('%d/%m/%Y'),  # Formata a data
                'observacao': atendimento[3],
                'usuario': atendimento[4],
            }
            for atendimento in atendimentos
        ]

        return atendimentos_dict
    except Exception as e:
        print(f"Erro ao carregar atendimentos: {e}")
        return []


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
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
            return redirect('/consulta')
        else:
            flash('Nome de usuário ou senha incorretos. Por favor, tente novamente.')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Limpa os dados da sessão ao fazer logout
    return render_template('index.html')
    

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    if 'usuario' not in session:  # Verifica se o usuário não está logado
        flash("Você precisa estar logado para acessar a consulta.")
        return redirect('/login')  # Redireciona para a página de login se não estiver logado

    if request.method == 'GET':
        data_hoje = date.today().strftime('%d/%m/%Y')
        try:
            conexao = criar_conexao()
            cursor = conexao.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT nome_cliente, cpf_cnpj, data_agendamento, observacao, usuario
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


    
        
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()  # Obtém o nome do formulário
        cpf_selecionado = request.form.get('cpf_selecionado', '').strip()  # CPF do cliente selecionado
        print(f"CPF Selecionado: {cpf_selecionado}")  # Verificação do CPF selecionado
        data_hoje = date.today().strftime('%Y-%m-%d')
        
        try:
            conexao = criar_conexao()
            cursor = conexao.cursor()
            atendimentos = []

            # Caso um CPF seja selecionado, busca os detalhes do cliente
            if cpf_selecionado:
                query_cliente = """
                    SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                    FROM clientes 
                    WHERE cpf_cnpj = %s AND ativo = 'S' 
                """
                cursor.execute(query_cliente, (cpf_selecionado,))
                cliente = cursor.fetchone()

                cpfs_relacionados = []
                clientes_relacionados = []  # Certifique-se de inicializar antes de usá-laT

                if cliente:  
                    cpfs_relacionados = [cliente[0]]  # Inicializa com o CPF do cliente principal

                    # Verifica se existem outros clientes com o mesmo nome
                    query_dublos = """
                        SELECT cpf_cnpj, nome_cliente, bairro
                        FROM clientes
                        WHERE nome_cliente = %s AND ativo = 'S' 
                    """
                    cursor.execute(query_dublos, (cliente[1],))
                    clientes_duplicados = cursor.fetchall()

                    if len(clientes_duplicados) > 1:  # Mais de um cliente com o mesmo nome
                        bairro_selecionado = cliente[3]  # Obtém o bairro do cliente selecionado

                        # Aplicação do filtro de bairro nos relacionados também
                        clientes_com_duplicata = []
                        for rel_cliente in clientes_duplicados:
                            if rel_cliente[0] != cliente[0]:  # Exclui o cliente selecionado da comparação
                                query_relacionados = """
                                    SELECT cpf_cnpj, nome_cliente, bairro
                                    FROM clientes
                                    WHERE responsavel = %s AND ativo = 'S'
                                """
                                cursor.execute(query_relacionados, (rel_cliente[0],))
                                relacionados = cursor.fetchall()

                                for relacionado in relacionados:
                                    if relacionado[1] in [cliente[1] for cliente in clientes_duplicados if cliente[0] != cliente[0]]:
                                        clientes_com_duplicata.append(relacionado)

                        # Filtra somente clientes com o mesmo nome
                        if clientes_com_duplicata:
                            clientes_relacionados = clientes_com_duplicata
                        else:
                            # Caso não existam duplicatas, todos os relacionados são retornados
                            query_relacionados = """
                                SELECT cpf_cnpj, nome_cliente, bairro
                                FROM clientes
                                WHERE responsavel = %s AND ativo = 'S'
                            """
                            cursor.execute(query_relacionados, (cliente[2],))
                            clientes_relacionados = cursor.fetchall()

                    else:
                        # Caso não existam duplicatas, todos os relacionados são retornados
                        query_relacionados = """
                            SELECT cpf_cnpj, nome_cliente, bairro
                            FROM clientes
                            WHERE responsavel = %s AND ativo = 'S'
                        """
                        cursor.execute(query_relacionados, (cliente[2],))
                        clientes_relacionados = cursor.fetchall()

                    print(f"Clientes relacionados: {clientes_relacionados}")

                    # Chama a função que carrega os atendimentos filtrados
                    atendimentos_filtrados = carregar_atendimentos(cpf_selecionado, [cliente[0] for cliente in clientes_relacionados])
                    print(f"Atendimentos carregados: {atendimentos_filtrados}")


                if cliente:  # Garante que o cliente foi encontrado
                    query_notas = """
                        SELECT DISTINCT
                            cr.empresa,
                            cr.nota,
                            cr.parcela,
                            cr.data_venda,
                            cr.data_vencimento,
                            cr.valor_original,
                            cr.saldo_devedor
                        FROM 
                            contas_a_receber cr
                        WHERE 
                            cr.cpf_cnpj = %s
                            AND cr.data_base = %s
                    """

                    cpf_cliente = cliente[0]  # CPF do cliente
                    nome_cliente = cliente[1]  # Nome do cliente
                    responsavel = cliente[2]
                    bairro_cliente = cliente[3]  # A variável 'bairro_cliente' deve conter o valor do bairro do cliente

                    cliente_detalhes = {
                        "cpf": cliente[0],
                        "nome": cliente[1],
                        "notas": [],
                        "atendimentos": atendimentos_filtrados  # Passando os atendimentos encontrados
                    }
                    
                    atendimentos_combinados = []
                    # Para cada cpf relacionado, combine os atendimentos
                    for cpf in cpfs_relacionados:
                        # Filtra os atendimentos por cpf
                        atendimentos_cliente = [atendimento for atendimento in atendimentos if atendimento['cpf_cnpj'] == cpf]
                        atendimentos_combinados.extend(atendimentos_cliente)

                     # Carregar os atendimentos de acordo com o CPF do cliente e seus relacionados
                    atendimentos_combinados = carregar_atendimentos(cpf_cliente, cpfs_relacionados)
                    cliente_detalhes["atendimentos"] = atendimentos_combinados


                    # Remove duplicatas nos atendimentos
                    atendimentos_deduplicados = list({f"{atd['cpf_cnpj']}_{atd['data_atendimento']}": atd for atd in atendimentos_combinados}.values())

                    # Atualiza o cliente_detalhes para incluir os atendimentos deduplicados
                    cliente_detalhes["atendimentos"] = atendimentos_deduplicados

                    cursor.execute(query_notas, (cpf_selecionado, data_hoje))
                    notas = cursor.fetchall()

                    data_hoje = date.today()

                    cliente_detalhes = {
                        "cpf": cpf_cliente,
                        "nome": nome_cliente,
                        "notas": sorted(
                            [
                                {
                                    "empresa": nota[0],
                                    "nota": nota[1],
                                    "parcela": nota[2],
                                    "data_venda": nota[3].strftime('%d/%m/%Y') if nota[3] else None,  # Mudança para '%Y'
                                    "data_vencimento": nota[4],  # Não use .date() aqui
                                    "valor_original": float(nota[5]) if nota[5] else 0.0,
                                    "saldo_devedor": float(nota[6]) if nota[6] else 0.0,
                                }
                                for nota in notas
                            ],
                            key=lambda x: (
                                x["data_vencimento"].year if x["data_vencimento"] else 9999,  # Ano
                                x["data_vencimento"].month if x["data_vencimento"] else 12,   # Mês
                                x["data_vencimento"].day if x["data_vencimento"] else 31      # Dia
                            )
                        ),
                    }
                    # Inicializa a lista de detalhes dos clientes relacionados
                    clientes_relacionados_detalhes = []

                    for clientes_relacionado in clientes_relacionados:
                        cpf_selecionado = clientes_relacionado[0]
                        nome_relacionado = clientes_relacionado[1]

                        cursor.execute(query_notas, (cpf_selecionado, data_hoje))
                        notas_relacionadas = cursor.fetchall()

                        # Adiciona os detalhes dos clientes relacionados à lista
                        clientes_relacionados_detalhes.append({
                            "cpf": cpf_selecionado,
                            "nome": nome_relacionado,
                            "notas": [
                                {
                                    "empresa": nota[0],
                                    "nota": nota[1],
                                    "parcela": nota[2],
                                    "data_venda": nota[3].strftime('%d/%m/%Y') if nota[3] else None,  # Mudança para '%Y'
                                    "data_vencimento": nota[4],  # Não use .date() aqui
                                    "valor_original": float(nota[5]) if nota[5] else 0.0,
                                    "saldo_devedor": float(nota[6]) if nota[6] else 0.0,
                                }
                                for nota in notas_relacionadas
                            ],
                        })

                    # Calcula o total a receber do cliente principal
                    total_a_receber = sum(
                        nota["saldo_devedor"] for nota in cliente_detalhes["notas"] if nota["saldo_devedor"]
                    )

                    # Adiciona o total a receber dos clientes relacionados (excluindo o CPF do cliente principal)
                    total_a_receber += sum(
                        nota["saldo_devedor"]
                        for cliente_relacionado in clientes_relacionados_detalhes
                        if cliente_relacionado["cpf"] != cliente_detalhes["cpf"]  # Somente para CPFs relacionados diferentes
                        for nota in cliente_relacionado["notas"]
                    )

                    # Exclui os clientes relacionados cujo CPF seja igual ao do cliente principal
                    clientes_relacionados_detalhes = [
                        cliente for cliente in clientes_relacionados_detalhes
                        if cliente["cpf"] != cliente_detalhes["cpf"]
                    ]

                    # Adiciona o total a receber ao cliente principal
                    cliente_detalhes['total_a_receber'] = f"R$ {total_a_receber:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                    # Cria a lista de clientes para exibição
                    clientes = [(cpf_cliente, nome_cliente)] + clientes_relacionados

                    # Debug: Imprime atendimentos filtrados antes de renderizar o template
                    print("Antes de retornar para o template:", atendimentos_filtrados)

                    # Retorna os dados para o template
                    return render_template(
                        'consulta.html',
                        clientes=clientes,
                        cliente_detalhes=cliente_detalhes,
                        clientes_relacionados_detalhes=clientes_relacionados_detalhes,
                        atendimentos=atendimentos_filtrados,
                        data_hoje=data_hoje
                    )

                    # Caso nenhum cliente seja encontrado
                    flash("Cliente não encontrado para o CPF selecionado.")
                    return render_template('consulta.html')

            # Pesquisa inicial por nome
            query = """
                SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                FROM clientes 
                WHERE (nome_cliente ILIKE %s OR responsavel ILIKE %s) AND ativo = 'S'
            """
            cursor.execute(query, (f"%{nome}%", f"%{nome}%"))
            clientes = cursor.fetchall()

            clientes_unicos = []
            seen = set()

            for cpf, nome, responsavel, bairro in clientes:
                chave_cliente = (nome, bairro)
                if chave_cliente not in seen:
                    seen.add(chave_cliente)
                    clientes_unicos.append((cpf, nome, responsavel, bairro))
                    
            if clientes_unicos:
                return render_template('consulta.html', data_hoje=data_hoje, clientes=clientes_unicos, atendimentos=atendimentos)

            return render_template('consulta.html')

        except Exception as e:
            print(f"Erro na consulta: {e}")
            flash("Ocorreu um erro na consulta.")
            return render_template('consulta.html')

        finally:
            if 'conexao' in locals():
                conexao.close()

    return render_template('consulta.html')

@app.route('/add_observation', methods=['POST'])
def adicionar_observacao():
    try:
        print("Dados recebidos:", request.form)

        # Captura os dados do formulário
        cliente_valor = request.form.get('cliente')
        if '|' in cliente_valor:
            cpf_cnpj, nome_cliente = cliente_valor.split('|')  # Extrai CPF e Nome
        else:
            return jsonify({"error": "Formato inválido para cliente"}), 400
            
        observacao = request.form.get('observation')
        data_atendimento = request.form.get('date')
        data_agendamento = request.form.get('agendamento')

        print(f"Observação: {observacao}, Data: {data_atendimento}, Nome: {nome_cliente}, CPF/CNPJ: {cpf_cnpj}, Agendamento: {data_agendamento}")

        # Verifica se todos os dados necessários estão presentes
        if not observacao or not data_atendimento or not nome_cliente or not cpf_cnpj:
            print("Erro: Dados incompletos")
            return jsonify({"error": "Dados incompletos"}), 400

        # Recupera o usuário logado
        usuario_logado = session.get('usuario')  # Supondo que você use session['usuario']
        if not usuario_logado:
            return jsonify({"error": "Usuário não logado"}), 400  # Garante que o usuário esteja logado

        print(f"Usuário logado: {usuario_logado}")

        # Cria uma conexão com o banco de dados
        conexao = criar_conexao()

        # Insere os dados na tabela "atendimentos"
        query = """
        INSERT INTO atendimentos (nome_cliente, cpf_cnpj, data_atendimento, observacao, usuario, data_agendamento)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (nome_cliente.strip(), cpf_cnpj.strip(), data_atendimento.strip(), observacao.strip(), usuario_logado.strip(), data_agendamento.strip() if data_agendamento else None)
        
        with conexao.cursor() as cursor:
            cursor.execute(query, valores)
            conexao.commit()  # Confirma a transação

        print(f"Observação adicionada com sucesso: {valores}")
        return jsonify({"success": "Observação adicionada com sucesso!"}), 200

    except Exception as e:
        # Caso ocorra um erro, exibir a mensagem no JSON
        print(f"Erro ao adicionar observação: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Fecha a conexão com o banco de dados
        if 'conexao' in locals() and conexao:
            conexao.close()

if __name__ == '__main__':
    app.run(debug=True)
