from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao, obter_notificacoes, liberar_conexao, login_required

contratos_bp = Blueprint('contratos', __name__)

@contratos_bp.route('/contratos')
@login_required
def contratos():

    usuario_logado = session['usuario']

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        cursor.execute("SELECT id, id_empresa FROM usuarios WHERE nome = %s", (usuario_logado,))
        resultado = cursor.fetchone()

        if resultado is None:
            flash("Usuário não encontrado")
            return redirect('/login')

        usuario_id, id_empresa = resultado

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
            SELECT id_cliente,
                nome_cliente, 
                documento, 
                data_geracao, 
                data_vencimento,
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
        
        print(lista)
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
def salvarcontrato():
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()



    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            liberar_conexao(conexao)