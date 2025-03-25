from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao

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

        cursor.execute("""
            SELECT 1 FROM acessos
            WHERE usuario_id = %s AND setor_id = 1
        """, (usuario_id,))

        if cursor.fetchone():  
            return render_template('gastos.html')  

        else:
            return render_template('home.html', erro_gastos=True)  

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            conexao.close()
