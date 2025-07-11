from flask import Blueprint, render_template, request, session, flash, redirect, jsonify
from functions import criar_conexao, obter_notificacoes, liberar_conexao, login_required

contratos_bp = Blueprint('contratos', __name__)

@contratos_bp.route('/contratos')
@login_required
def contratos():
    usuario_logado = session.get('usuario')
    usuario_id = session.get('usuario_id')
    id_empresa = session.get('id_empresa')

    if not usuario_logado or not usuario_id or not id_empresa:
        flash("Sessão inválida. Por favor, faça login novamente.")
        return redirect('/login')

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT 1 FROM acessos
            WHERE usuario_id = %s AND setor_id = 2
        """, (usuario_id,))
        acesso = cursor.fetchone()

        if not acesso:
            flash("Você não tem acesso a essa área.")
            return redirect('/home')

        session['notificacoes'] = obter_notificacoes(usuario_logado)

        query = """
            SELECT id,
                id_cliente,
                nome_cliente, 
                documento, 
                TO_CHAR(data_geracao, 'DD/MM/YYYY') AS data_geracaof,
                TO_CHAR(data_vencimento, 'DD/MM/YYYY') AS data_vencimentof,
                valor_original, 
                saldo_devedor, 
                tipo_contrato
            FROM contratos
            WHERE id_empresa = %s
        """.strip()

        cursor.execute(query, (id_empresa,))
        colunas = [desc[0] for desc in cursor.description]
        contratos = cursor.fetchall()

        lista = []
        for linha in contratos:
            linha_dict = dict(zip(colunas, linha))
            lista.append(linha_dict)
        
        cursor.close()
        
        return render_template(
            'contratos.html',
            notificacoes=session['notificacoes'],
            lista=lista
        )  

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            liberar_conexao(conexao)

@contratos_bp.route('/salvarcontrato', methods=['POST'])
@login_required
def salvarcontrato():
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        dados = request.get_json()
        valor = dados['valor_original'].replace(',', '.').strip()
        saldo = dados['saldo_devedor'].replace(',', '.').strip()
        id_empresa = session.get('id_empresa')
        contrato_id = dados.get('id')

        if contrato_id:
            cursor.execute("""
                UPDATE contratos SET
                    id_cliente = %s,
                    nome_cliente = %s,
                    documento = %s,
                    data_geracao = %s,
                    data_vencimento = %s,
                    valor_original = %s,
                    saldo_devedor = %s,
                    tipo_contrato = %s
                WHERE id = %s 
            """, (
                dados['id_cliente'],
                dados['nome_cliente'],
                dados['documento'],
                dados['data_geracao'],
                dados['data_vencimento'],
                valor,
                saldo,
                dados['tipo_contrato'],
                contrato_id
            ))
        else:
            cursor.execute("""
                INSERT INTO contratos (
                    id_cliente,
                    nome_cliente,
                    documento,
                    data_geracao,
                    data_vencimento,
                    valor_original,
                    saldo_devedor,
                    tipo_contrato,
                    id_empresa
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dados['id_cliente'],
                dados['nome_cliente'],
                dados['documento'],
                dados['data_geracao'],
                dados['data_vencimento'],
                valor,
                saldo,
                dados['tipo_contrato'],
                id_empresa
            ))
        
        conexao.commit()
        return jsonify({'mensagem': 'Contrato salvo com sucesso!'})

    except Exception as e:
        print("Erro ao salvar contrato:", e)
        return jsonify({'mensagem': 'Erro ao salvar contrato.'}), 500
    finally:
        if conexao:
            liberar_conexao(conexao)

@contratos_bp.route('/deletarcontrato', methods=['POST'])
@login_required
def deletarcontrato():
    conexao = None
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        dados = request.get_json()
        contrato_id = dados.get('id')

        cursor.execute("""
            DELETE FROM contratos WHERE id = %s
        """, (contrato_id,))

        conexao.commit()
        return jsonify({'mensagem': 'Contrato excluído com sucesso!'})

    except Exception as e:
        print("Erro ao deletar contrato:", e)
        return jsonify({'mensagem': 'Erro ao deletar contrato.'}), 500
    finally:
        if conexao:
            liberar_conexao(conexao)