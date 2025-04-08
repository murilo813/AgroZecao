from flask import Flask, Blueprint, render_template, request, redirect, session, flash, jsonify
from markupsafe import Markup
from datetime import date
from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
import psycopg2
import json
from functions import carregar_atendimentos, criar_conexao

consulta_bp = Blueprint('consulta', __name__)

@consulta_bp.route('/consulta', methods=['GET', 'POST'])
def consulta():
    if 'usuario' not in session:  
        flash("Você precisa estar logado para acessar a consulta.")
        return redirect('/login')  

    usuario_logado = session['usuario']

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE nome = %s", (usuario_logado,))
        usuario_id = cursor.fetchone()

        if not usuario_id:
            flash("Usuário não encontrado.")
            return redirect('/login')

        usuario_id = usuario_id[0] 

        cursor.execute("""
            SELECT 1 FROM acessos
            WHERE usuario_id = %s AND setor_id = 2
        """, (usuario_id,))

        if not cursor.fetchone():  
            return render_template('home.html', erro_financeiro=True)  

        cpf_url = request.args.get('cpf_cnpj', '').strip() if request.method == 'GET' else None

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    
    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()

    if cpf_url:
        cpf_selecionado = cpf_url  
        nome = ""  
        request.method = 'POST'  
 
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()  
        cpf_selecionado = request.form.get('cpf_selecionado', '').strip() or request.args.get('cpf_cnpj', '').strip()
        data_hoje = date.today().strftime('%Y-%m-%d')
        
        try:
            conexao = criar_conexao()
            cursor = conexao.cursor()
            atendimentos = []

            if cpf_selecionado:
                if len(cpf_selecionado) >= 11 and cpf_selecionado.isdigit():  
                    query_cliente = """
                        SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                        FROM clientes 
                        WHERE cpf_cnpj = %s AND ativo = 'S' 
                    """
                    cursor.execute(query_cliente, (cpf_selecionado,))
                    cliente = cursor.fetchone()
                else:  
                    query_cliente = """
                        SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                        FROM clientes
                        WHERE id_cliente = %s AND ativo = 'S'
                    """
                    cursor.execute(query_cliente, (cpf_selecionado,))
                    cliente = cursor.fetchone()

                    if cliente:
                        cpf_selecionado = cliente[0]  

            elif nome:  
                query_cliente = """
                    SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                    FROM clientes
                    WHERE cpf_cnpj = %s AND ativo = 'S'
                """
                cursor.execute(query_cliente, (nome,))
                cliente = cursor.fetchone()
            if cpf_selecionado and not cpf_selecionado.isdigit():
                cpf_selecionado = cliente[0] 

            cpfs_relacionados = [cpf_selecionado] if cpf_selecionado else []
            clientes_relacionados = []

            if cliente:  
                cpfs_relacionados = [cliente[0]] 

                query_dublos = """
                    SELECT cpf_cnpj, nome_cliente, bairro
                    FROM clientes
                    WHERE nome_cliente = %s AND ativo = 'S' 
                """
                cursor.execute(query_dublos, (cliente[1],))
                clientes_duplicados = cursor.fetchall()

                if len(clientes_duplicados) > 1:  
                    bairro_selecionado = cliente[3]  
                    
                    clientes_com_duplicata = []
                    for rel_cliente in clientes_duplicados:
                        if rel_cliente[0] != cliente[0]:  
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

                    if clientes_com_duplicata:
                        clientes_relacionados = clientes_com_duplicata
                    else:
                        query_relacionados = """
                            SELECT cpf_cnpj, nome_cliente, bairro
                            FROM clientes
                            WHERE responsavel = %s AND ativo = 'S'
                        """
                        cursor.execute(query_relacionados, (cliente[2],))
                        clientes_relacionados = cursor.fetchall()

                else:
                    query_relacionados = """
                        SELECT cpf_cnpj, nome_cliente, bairro
                        FROM clientes
                        WHERE responsavel = %s AND ativo = 'S'
                    """
                    cursor.execute(query_relacionados, (cliente[2],))
                    clientes_relacionados = cursor.fetchall()
                atendimentos_filtrados = carregar_atendimentos(cpf_selecionado, [cliente[0] for cliente in clientes_relacionados])

                if cliente:  
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

                    cpf_cliente = cliente[0]  
                    nome_cliente = cliente[1]  
                    responsavel = cliente[2]
                    bairro_cliente = cliente[3]  

                    cliente_detalhes = {
                        "cpf": cliente[0],
                        "nome": cliente[1],
                        "notas": [],
                        "atendimentos": atendimentos_filtrados 
                    }
            
                    atendimentos_combinados = []
                    for cpf in cpfs_relacionados:
                        atendimentos_cliente = [atendimento for atendimento in atendimentos if atendimento['cpf_cnpj'] == cpf]
                        atendimentos_combinados.extend(atendimentos_cliente)

                    atendimentos_combinados = carregar_atendimentos(cpf_cliente, cpfs_relacionados)
                    cliente_detalhes["atendimentos"] = atendimentos_combinados

                    atendimentos_deduplicados = list({f"{atd['cpf_cnpj']}_{atd['data_atendimento']}": atd for atd in atendimentos_combinados}.values())

                    cliente_detalhes["atendimentos"] = atendimentos_deduplicados

                    cursor.execute(query_notas, (cpf_selecionado, data_hoje))
                    notas = cursor.fetchall()
                    data_hoje = date.today()

                    cliente_detalhes = {
                        "cpf": cpf_cliente,
                        "nome": nome_cliente,
                        "notas": sorted( #Coloca na ordem da data vencimento
                            [
                                {
                                    "empresa": nota[0],
                                    "nota": nota[1],
                                    "parcela": nota[2],
                                    "data_venda": nota[3].strftime('%d/%m/%Y') if nota[3] else None,  
                                    "data_vencimento": nota[4],  
                                    "valor_original": float(nota[5]) if nota[5] else 0.0,
                                    "saldo_devedor": float(nota[6]) if nota[6] else 0.0,
                                }
                                for nota in notas
                            ],
                            key=lambda x: (
                                x["data_vencimento"].year if x["data_vencimento"] else 9999,  
                                x["data_vencimento"].month if x["data_vencimento"] else 12,   
                                x["data_vencimento"].day if x["data_vencimento"] else 31      #Os valores são considerados assim para garantir que as notas sem data de vencimento fiquem por último.
                            )
                        ),
                    }
                    clientes_relacionados_detalhes = []
                    notas_relacionadas_geral = []

                    for clientes_relacionado in clientes_relacionados:
                        cpf_selecionado = clientes_relacionado[0]
                        nome_relacionado = clientes_relacionado[1]

                        cursor.execute(query_notas, (cpf_selecionado, data_hoje))
                        notas_relacionadas = cursor.fetchall()

                        clientes_relacionados_detalhes.append({
                            "cpf": cpf_selecionado,
                            "nome": nome_relacionado,
                            "notas": [
                                {
                                    "empresa": nota[0],
                                    "nota": nota[1],
                                    "parcela": nota[2],
                                    "data_venda": nota[3].strftime('%d/%m/%Y') if nota[3] else None,  
                                    "data_vencimento": nota[4],  
                                    "valor_original": float(nota[5]) if nota[5] else 0.0,
                                    "saldo_devedor": float(nota[6]) if nota[6] else 0.0,
                                }
                                for nota in notas_relacionadas
                            ],
                        })

                    notas_dos_relacionados = [
                        (nota["empresa"], nota["nota"])
                        for cliente in clientes_relacionados_detalhes
                        for nota in cliente["notas"]
                    ]
                    if notas_dos_relacionados:
                        cursor.execute("""
                            SELECT empresa, nota, obs
                            FROM obs_nota
                            WHERE (empresa, nota) IN %s
                        """, (tuple(notas_dos_relacionados),))

                        obs_dict_relacionados = {(empresa, nota): obs for empresa, nota, obs in cursor.fetchall()}

                        for cliente in clientes_relacionados_detalhes:
                            for nota in cliente["notas"]:
                                nota["obs"] = obs_dict_relacionados.get((nota["empresa"], nota["nota"]), "")
                    #É usado o saldo_devedor pois é com ele que é feito o cálculo de quanto o cliente ainda deve.
                    total_a_receber = sum(
                        nota["saldo_devedor"] for nota in cliente_detalhes["notas"] if nota["saldo_devedor"]
                    )

                    total_a_receber += sum(
                        nota["saldo_devedor"]
                        for cliente_relacionado in clientes_relacionados_detalhes
                        if cliente_relacionado["cpf"] != cliente_detalhes["cpf"]  
                        for nota in cliente_relacionado["notas"]
                    )

                    clientes_relacionados_detalhes = [
                        cliente for cliente in clientes_relacionados_detalhes
                        if cliente["cpf"] != cliente_detalhes["cpf"]
                    ]

                    cliente_detalhes['total_a_receber'] = f"R$ {total_a_receber:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                    clientes = [(cpf_cliente, nome_cliente)] + clientes_relacionados

                    return render_template(
                        'consulta.html',
                        clientes=clientes,
                        cliente_detalhes=cliente_detalhes,
                        clientes_relacionados_detalhes=clientes_relacionados_detalhes,
                        atendimentos=atendimentos_filtrados,
                        data_hoje=data_hoje
                    )

                    flash("Cliente não encontrado para o CPF selecionado.")
                    return render_template('consulta.html')

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

@consulta_bp.route('/salvar_obs_notas', methods=['POST'])
def salvar_obs_notas():
    try:
        data = request.get_json()
        obs_notas = data.get('obs_notas')  

        conexao = criar_conexao()
        with conexao.cursor() as cursor:
            for obs in obs_notas:
                empresa = obs.get("empresa")
                nota = obs.get("nota")
                observacao = obs.get("observacao")

                if empresa and nota:
                    if observacao.strip() != "":
                        cursor.execute("""
                            INSERT INTO obs_nota (empresa, nota, obs)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (empresa, nota) DO UPDATE SET obs = EXCLUDED.obs
                        """, (empresa, nota, observacao))
                    else:
                        cursor.execute("""
                            DELETE FROM obs_nota
                            WHERE empresa = %s AND nota = %s
                        """, (empresa, nota))

            conexao.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        print("Erro ao salvar observações via sendBeacon:", e)
        return jsonify({"status": "erro"}), 500

@consulta_bp.route('/add_observation', methods=['POST'])
def adicionar_observacao():
    try:
        cliente_valor = request.form.get('cliente')
        if '|' in cliente_valor:
            cpf_cnpj, nome_cliente = cliente_valor.split('|')  
        else:
            return jsonify({"error": "Formato inválido para cliente"}), 400
            
        observacao = request.form.get('observation')
        data_atendimento = request.form.get('date')
        data_agendamento = request.form.get('agendamento')
        estado = "ativa"

        if not observacao or not data_atendimento or not nome_cliente or not cpf_cnpj:
            print("Erro: Dados incompletos")
            return jsonify({"error": "Dados incompletos"}), 400

        usuario_logado = session.get('usuario') 
        if not usuario_logado:
            return jsonify({"error": "Usuário não logado"}), 400  

        conexao = criar_conexao()

        with conexao.cursor() as cursor:
            # Inserir atendimento
            query_atendimento = """
            INSERT INTO atendimentos (nome_cliente, cpf_cnpj, data_atendimento, observacao, usuario)
            VALUES (%s, %s, %s, %s, %s)
            """
            valores_atendimento = (nome_cliente.strip(), cpf_cnpj.strip(), data_atendimento.strip(), observacao.strip(), usuario_logado.strip())
            cursor.execute(query_atendimento, valores_atendimento)
            conexao.commit()

            # Buscar CPFs relacionados
            cpfs_relacionados = [cpf_cnpj.strip()]
            clientes_relacionados = []

            query_cliente = """
                SELECT cpf_cnpj, nome_cliente, bairro, responsavel
                FROM clientes
                WHERE cpf_cnpj = %s AND ativo = 'S'
            """
            cursor.execute(query_cliente, (cpf_cnpj.strip(),))
            cliente = cursor.fetchone()

            if cliente:
                cpfs_relacionados = [cliente[0]]

                query_dublos = """
                    SELECT cpf_cnpj, nome_cliente, bairro
                    FROM clientes
                    WHERE nome_cliente = %s AND ativo = 'S'
                """
                cursor.execute(query_dublos, (cliente[1],))
                clientes_duplicados = cursor.fetchall()

                if len(clientes_duplicados) > 1:
                    bairro_selecionado = cliente[2]

                    clientes_com_duplicata = []
                    for rel_cliente in clientes_duplicados:
                        if rel_cliente[0] != cliente[0]:  
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

                    if clientes_com_duplicata:
                        clientes_relacionados = clientes_com_duplicata
                    else:
                        query_relacionados = """
                            SELECT cpf_cnpj, nome_cliente, bairro
                            FROM clientes
                            WHERE responsavel = %s AND ativo = 'S'
                        """
                        cursor.execute(query_relacionados, (cliente[3],))
                        clientes_relacionados = cursor.fetchall()

                else:
                    query_relacionados = """
                        SELECT cpf_cnpj, nome_cliente, bairro
                        FROM clientes
                        WHERE responsavel = %s AND ativo = 'S'
                    """
                    cursor.execute(query_relacionados, (cliente[3],))
                    clientes_relacionados = cursor.fetchall()

                for relacionado in clientes_relacionados:
                    if relacionado[0] not in cpfs_relacionados:
                        cpfs_relacionados.append(relacionado[0])

            # Se houver um agendamento, verificar notificações ativas e inserir a nova
            if data_agendamento:
                query_verifica = """
                SELECT id_not FROM not_gerencia
                WHERE cpf_cnpj = ANY(%s) AND estado = 'ativa'
                """
                cursor.execute(query_verifica, (cpfs_relacionados,))
                notificacoes_ativas = cursor.fetchall()

                # Se existir, atualizar para "inativa"
                if notificacoes_ativas:
                    ids_notificacoes = tuple(noti[0] for noti in notificacoes_ativas)
                    query_inativar = """
                    UPDATE not_gerencia SET estado = 'inativa'
                    WHERE id_not IN %s
                    """
                    cursor.execute(query_inativar, (ids_notificacoes,))
                    conexao.commit()

                # Inserir nova notificação
                query_gerencia = """
                INSERT INTO not_gerencia (nome_cliente, cpf_cnpj, data, anotacao, criador, data_agendamento, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                valores_gerencia = (nome_cliente.strip(), cpf_cnpj.strip(), data_atendimento.strip(), observacao.strip(), usuario_logado.strip(), data_agendamento.strip(), estado)
                cursor.execute(query_gerencia, valores_gerencia)
                conexao.commit()

        return jsonify({"success": "Observação adicionada com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao adicionar observação: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if 'conexao' in locals() and conexao:
            conexao.close()