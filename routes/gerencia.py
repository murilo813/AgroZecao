from flask import Blueprint, render_template, request, session, flash, redirect
from functions import criar_conexao

gerencia_bp = Blueprint('gerencia', __name__)

@gerencia_bp.route('/gerencia')
def gerencia():
    if 'usuario' not in session:  
        flash("Você precisa estar logado para acessar a página de Gerência.")
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
            WHERE usuario_id = %s AND setor_id = 3
        """, (usuario_id,))

        if cursor.fetchone():  
            return render_template('gerencia.html')  

        else:
            return render_template('home.html', erro_gerencia=True)  

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if conexao:
            conexao.close()

@gerencia_bp.route('/add_notificacao', methods=['POST'])
def adicionar_notificacao():
    try:
        usuario = request.form.get('usuario')
        anotacao = request.form.get('anotacao')

        if not usuario or not anotacao:
            return jsonify({"error": "Dados incompletos"}), 400
        
        usuario_logado = session.get('usuario')
        if not usuario_logado:
            return jsonify({"error":"Usuário não logado"}), 400

        conexao = criar_conexao()

        query = """
        INSERT INTO AINDA IREI FAZER
        VALUES (%s, %s, %s)
        """
        valores = (usuario.strip(), anotacao.strip(), usuario_logado.strip())

        with conexao.cursor() as cursor:
            cursor.execute(query, valores)
            conexao.commit()

        return jsonify({"sucess": "Notificação enviada com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'conexao' in locals() and conexao:
            conexao.close()