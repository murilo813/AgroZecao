from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao, obter_notificacoes

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

        cursor.execute("SELECT nome_cliente FROM clientes WHERE tipo_pessoa = 'J' AND perfil_for = true")
        fornecedor_tuplas = cursor.fetchall()
        fornecedor = [f[0] for f in fornecedor_tuplas]  

        session['notificacoes'] = obter_notificacoes(usuario_logado)

        return render_template('gastos.html',
                            notificacoes=session['notificacoes'],
                            placas=placas,
                            responsaveis=responsaveis,
                            vinculos=vinculos,
                            fornecedor=fornecedor)

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            conexao.close()
