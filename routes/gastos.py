from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao, obter_notificacoes
from datetime import datetime
import psycopg2
import os

gastos_bp = Blueprint('gastos', __name__)

@gastos_bp.route('/gastos')
def gastos():
    if 'usuario' not in session:  
        flash("Você precisa estar logado para acessar a página de gastos.")
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

        cursor.execute("SELECT 1 FROM acessos WHERE usuario_id = %s AND setor_id = 5", (usuario_id,))
        tem_acesso = cursor.fetchone()

        if not tem_acesso:
            return render_template('home.html', erro_gastos=True)  

        cursor.execute("SELECT placa, responsavel FROM frota ORDER BY placa")
        frota = cursor.fetchall()  

        placas = sorted(list(set([f[0] for f in frota])))
        responsaveis = sorted(list(set([f[1] for f in frota])))

        vinculos = {placa: resp for placa, resp in frota}

        cursor.execute("""
            SELECT nome_cliente, cpf_cnpj
            FROM clientes
            WHERE tipo_pessoa = 'J'
            AND perfil_for = true
            AND nome_cliente ~ '^[^0-9]*[0-9]?[^0-9]*$'
        """)        
        fornecedor_tuplas = cursor.fetchall()
        fornecedor = [{'nome': f[0], 'cnpj': f[1]} for f in fornecedor_tuplas]

        cursor.execute("""
            SELECT
                placa,
                responsavel,
                tipo_gasto AS gasto,
                fornecedor AS onde,
                doc AS documento,
                TO_CHAR(data, 'DD/MM/YYYY') AS dia,
                valor_total AS valor,
                km,
                id_produto AS id_pro,
                produto,
                valor_produto AS valor_unit,
                quantidade,
                total_produto AS total
            FROM gastos
            ORDER BY documento, id_pro
        """)
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        dados = []
        doc_anterior = None
        tipo_gasto_anterior = None

        for linha in registros:
            linha_dict = dict(zip(colunas, linha))
            linha_dict = {k: ("" if v is None else v) for k, v in linha_dict.items()}
            doc_atual = linha_dict['documento']
            tipo_gasto_atual = linha_dict['gasto']  

            if doc_atual == doc_anterior and tipo_gasto_atual == tipo_gasto_anterior:
                linha_dict['placa_exibir'] = ''
                linha_dict['responsavel_exibir'] = ''
                linha_dict['gasto_exibir'] = ''
                linha_dict['onde_exibir'] = ''
                linha_dict['documento_exibir'] = ''
                linha_dict['dia_exibir'] = ''
                linha_dict['valor_exibir'] = ''
                linha_dict['km_exibir'] = ''
            else:
                linha_dict['placa_exibir'] = linha_dict['placa']
                linha_dict['responsavel_exibir'] = linha_dict['responsavel']
                linha_dict['gasto_exibir'] = linha_dict['gasto']
                linha_dict['onde_exibir'] = linha_dict['onde']
                linha_dict['documento_exibir'] = linha_dict['documento']
                linha_dict['dia_exibir'] = linha_dict['dia']
                linha_dict['valor_exibir'] = linha_dict['valor']
                linha_dict['km_exibir'] = linha_dict['km']
                doc_anterior = doc_atual
                tipo_gasto_anterior = tipo_gasto_atual

            dados.append(linha_dict)

        session['notificacoes'] = obter_notificacoes(usuario_logado)

        return render_template('gastos.html',
                            notificacoes=session['notificacoes'],
                            placas=placas,
                            responsaveis=responsaveis,
                            vinculos=vinculos,
                            fornecedor=fornecedor,
                            dados=dados) 

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            conexao.close()


@gastos_bp.route('/registrargastos', methods=["POST"])
def registrargastos():
    try:
        placa = request.form['placa']
        responsavel = request.form['responsavel']
        tipo_gasto = request.form['gasto'].upper()
        fornecedor = request.form['onde']
        doc = request.form['documento']
        data = request.form['dia']
        valor_total = request.form['valor'].replace('R$', '').replace('.', '').replace(',', '.').strip()
        desconto = request.form['desconto'].replace('R$', '').replace('.', '').replace(',', '.').strip()
        km = request.form['km'].replace('.', '').strip()

        ids_produto = request.form.getlist('id_pro[]')
        produtos = request.form.getlist('produto[]')
        valores_unit = request.form.getlist('valor_unit[]')
        quantidades = request.form.getlist('quantidade[]')  # <- isso estava faltando
        totais_produto = request.form.getlist('total[]')

        conn = criar_conexao()
        cur = conn.cursor()

        for i in range(len(produtos)):
            if not produtos[i].strip():
                continue  

            valor_prod = valores_unit[i].replace('R$', '').replace('.', '').replace(',', '.').strip()
            total_prod = totais_produto[i].replace('R$', '').replace('.', '').replace(',', '.').strip()
            qtd = quantidades[i].strip() or '0'

            cur.execute("""
                INSERT INTO gastos (
                    placa, responsavel, tipo_gasto, fornecedor, doc, data, valor_total, km,
                    id_produto, produto, valor_produto, quantidade, total_produto, desconto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                placa,
                responsavel,
                tipo_gasto,
                fornecedor,
                doc,
                datetime.strptime(data, '%Y-%m-%d').date(),
                valor_total,
                int(km) if km else None,
                ids_produto[i],
                produtos[i],
                valor_prod,
                qtd,  
                total_prod,
                desconto
            ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/gastos')  

    except Exception as e:
        print(f"Erro ao registrar gastos: {e}")
        return "Erro ao registrar dados", 500
