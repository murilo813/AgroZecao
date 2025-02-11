from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao

gerencia_bp = Blueprint('gerencia', __name__)


@gerencia_bp.route('/gerencia')
def gerencia():
    if 'usuario' not in session:  # Verifica se o usuário não está logado
        flash("Você precisa estar logado para acessar a página de Gerência.")
        return redirect('/login')  # Redireciona para a página de login se não estiver logado

    # Recupera o nome do usuário logado
    usuario_logado = session['usuario']

    try:
        # Cria a conexão com o banco de dados
        conexao = criar_conexao()
        cursor = conexao.cursor()

        # Consulta o id do usuário logado
        cursor.execute("SELECT id FROM usuarios WHERE nome = %s", (usuario_logado,))
        usuario_id = cursor.fetchone()

        if not usuario_id:
            flash("Usuário não encontrado.")
            return redirect('/login')

        usuario_id = usuario_id[0]  # Pega o ID do usuário

        # Verifica se o usuário tem acesso ao setor 'Gerência' (id = 3)
        cursor.execute("""
            SELECT 1 FROM acessos
            WHERE usuario_id = %s AND setor_id = 3
        """, (usuario_id,))

        if cursor.fetchone():  # Se o usuário tem acesso ao setor de Gerência
            return render_template('gerencia.html')  # Renderiza a página de consulta (ou outra específica para Gerência)

        else:
            return render_template('home.html', erro_gerencia=True)  # Passa o erro de acesso para o template home.html

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            conexao.close()
