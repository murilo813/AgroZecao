from flask import Blueprint, render_template, request, session, flash, redirect, jsonify
from functions import criar_conexao, obter_notificacoes, liberar_conexao, login_required
from datetime import date

gerencia_bp = Blueprint('gerencia', __name__)

@gerencia_bp.route('/gerencia')
@login_required
def gerencia(): 

    usuario_logado = session['usuario']

    try:
        conexao = criar_conexao()
        if not conexao:
            flash("Erro ao conectar ao banco de dados.")
            return redirect('/gerencia')

        cursor = conexao.cursor()

        cursor.execute("SELECT id_empresa FROM usuarios WHERE nome = %s", (usuario_logado,))
        usuario_empresa = cursor.fetchone()
        if not usuario_empresa:
            flash("Usuário não encontrado.")
            return redirect('/login')

        id_empresa = usuario_empresa[0]

        cursor.execute("SELECT nomeclatura FROM usuarios WHERE id_empresa = %s", (id_empresa,))
        usuarios = [row[0] for row in cursor.fetchall()]

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

        session['notificacoes'] = obter_notificacoes(usuario_logado)

        if cursor.fetchone():  
            return render_template('gerencia.html', usuarios=usuarios, notificacoes=session['notificacoes'])  

        else:
            return render_template('home.html', erro_gerencia=True)  

    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        flash("Erro ao verificar acesso. Tente novamente.")
        return redirect('/home')
    finally:
        if cursor:
            cursor.close()
        if conexao:
            liberar_conexao(conexao)

@gerencia_bp.route('/add_notificacao', methods=['POST'])
def adicionar_notificacao():
    try:
        usuario = request.form.get('usuario')
        anotacao = request.form.get('anotacao')
        estado = "ativa"

        if not usuario or not anotacao:
            return jsonify({"error": "Dados incompletos"}), 400
        
        usuario_logado = session.get('usuario')
        if not usuario_logado:
            return jsonify({"error":"Usuário não logado"}), 400

        conexao = criar_conexao()
        cursor = conexao.cursor()
        data_hoje = date.today()

        query = """
            SELECT nomeclatura
            FROM usuarios
            WHERE nome = %s
        """
        cursor.execute(query, (usuario_logado,))
        resultado = cursor.fetchone()
        nomeclatura = resultado[0] if resultado else 'Usuário'
        session['nomeclatura'] = nomeclatura

        cursor.execute("SELECT nome FROM usuarios WHERE nomeclatura = %s", (usuario,))
        usuario_nome = cursor.fetchone()
        usuario_nome = usuario_nome[0]

        query = """
        INSERT INTO not_gerencia (usuario, anotacao, criador, data, estado)
        VALUES (%s, %s, %s, %s, %s)
        """
        valores = (usuario_nome.strip(), anotacao.strip(), nomeclatura.strip(), data_hoje, estado)

        cursor.execute(query, (valores))
        conexao.commit()

        return jsonify({"success": "Notificação enviada com sucesso!"}), 200

    except Exception as e:
        return redirect('/gerencia')

    finally:
        if 'conexao' in locals() and conexao:
            liberar_conexao(conexao)

@gerencia_bp.route('/cobrancas', methods=['GET'])
def cobrancas():
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()
        data_hoje = date.today()
        usuario_logado = session['usuario']

        query_id_empresa = """
            SELECT id_empresa FROM usuarios WHERE nome = %s
        """
        cursor.execute(query_id_empresa, (usuario_logado,))
        id_empresa = cursor.fetchone()
        id_empresa = id_empresa[0]

        query_atendimentos = """
            SELECT a.nome_cliente, a.observacao, a.usuario
            FROM atendimentos a
            INNER JOIN usuarios u ON a.usuario = u.nome
            WHERE a.data_atendimento = %s
            AND u.id_empresa = %s
            ORDER BY a.data_atendimento ASC
        """
        
        cursor.execute(query_atendimentos, (data_hoje, id_empresa))
        atendimentos = cursor.fetchall()

        return jsonify({"atendimentos": atendimentos})
    
    except Exception as e:
        print(f"Erro ao carregar atendimentos: {e}")
        return jsonify({"atendimentos": []})
    finally:
        if cursor:
            cursor.close()
        if conexao:
            liberar_conexao(conexao)