from flask import Flask, Blueprint, render_template, request, redirect, session, flash, jsonify
from markupsafe import Markup
from datetime import date
from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
import psycopg2
import json
from functions import carregar_atendimentos, criar_conexao, obter_notificacoes, login_required, liberar_conexao

financeiro_bp = Blueprint('financeiro', __name__)

@financeiro_bp.route('/financeiro', methods=['GET', 'POST'])
@login_required
def financeiro():
    usuario_logado = session['usuario']
    session['notificacoes'] = obter_notificacoes(usuario_logado)
    id_empresa = session.get('id_empresa')

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
            WHERE usuario_id = %s AND (setor_id = 2 OR setor_id = 6)
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
            liberar_conexao(conexao)

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

            if not cpf_selecionado:
                query = """
                    SELECT cpf_cnpj, nome_cliente, responsavel, bairro
                    FROM clientes 
                    WHERE (nome_cliente ILIKE %s OR responsavel ILIKE %s) AND ativo = 'S'
                """
                cursor.execute(query, (f"%{nome}%", f"%{nome}%"))
                clientes = cursor.fetchall()

                return render_template('financeiro.html', notificacoes=session['notficacoes'], data_hoje=data_hoje, clientes=clientes)

            else:
                if len(cpf_selecionado) >= 11 and cpf_selecionado.isdigit():
                    query_cliente = """
                        SELECT responsavel
                        FROM clientes
                        WHERE cpf_cnpj = %s AND ativo = 'S'
                    """
                    cursor.execute(query_cliente, (cpf_selecionado,))
                    cliente = cursor.fetchone()
                else:
                    query_cliente = """
                        SELECT responsavel
                        FROM clientes
                        WHERE id_cliente = %s AND ativo = 'S'
                    """
                    cursor.execute(query_cliente, (cpf_selecionado,))                    
                    cliente = cursor.fetchone()

            if cliente:
                query_clientes = """
                    SELECT cpf_cnpj, nome_cliente, bairro
                    FROM clientes
                    WHERE responsavel = %s AND ativo = 'S'
                """
                cursor.execute(query_clientes, (cliente,))
                clientes = cursor.fetchall()

                lista_clientes_detalhes = []
                data_hoje = date.today()

                for cliente in clientes:
                    cpf_cliente = cliente[0]
                    nome_cliente = cliente[1]
                    bairro_cliente = cliente[2]

                    query_notas = """
                        SELECT
                            cr.empresa,
                            cr.nota,
                            cr.parcela,
                            cr.data_venda,
                            cr.data_vencimento,
                            cr.valor_original,
                            cr.saldo_devedor,
                            cr.tipo
                        FROM contas_a_receber cr
                        WHERE cr.cpf_cnpj = %s AND cr.data_base = %s
                    """
                    cursor.execute(query_notas, (cpf_cliente, data_hoje))
                    notas = cursor.fetchall()

                    cpfs = list({c[0] for c in clientes})
                    atendimentos_combinados = carregar_atendimentos(cpfs)

                    atendimentos_deduplicados = list({
                        f"{a['cpf_cnpj']}_{a['data_atendimento']}": a
                        for a in atendimentos_combinados
                    }.values())

                    cliente_detalhes = {
                        "cpf": cpf_cliente,
                        "nome": nome_cliente,
                        "bairro": bairro_cliente,
                        "notas": sorted(
                            [
                                {
                                    "empresa": nota[0],
                                    "nota": nota[1],
                                    "parcela": nota[2],
                                    "data_venda": nota[3].strftime('%d/%m/%Y') if nota[3] else None,  
                                    "data_vencimento": nota[4],  
                                    "valor_original": float(nota[5]) if nota[5] else 0.0,
                                    "saldo_devedor": float(nota[6]) if nota[6] else 0.0,
                                    "tipo": nota[7]
                                }
                                for nota in notas
                            ],
                            key=lambda x: (
                                x["data_vencimento"].year if x["data_vencimento"] else 9999,  
                                x["data_vencimento"].month if x["data_vencimento"] else 12,   
                                x["data_vencimento"].day if x["data_vencimento"] else 31
                            )
                        ),
                        "atendimentos": atendimentos_deduplicados
                    }

                    lista_clientes_detalhes.append(cliente_detalhes)










        except Exception as e:
            print(f"Erro na consulta: {e}")
            flash("Ocorreu um erro na consulta.")
            return render_template('financeiro.html')

        finally:
            if 'conexao' in locals():
                liberar_conexao(conexao)

    return render_template('financeiro.html', notificacoes=session['notificacoes'])