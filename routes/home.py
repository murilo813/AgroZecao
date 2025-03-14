from flask import Blueprint, session, flash, redirect, render_template, request, jsonify
from functions import criar_conexao, obter_notificacoes
from datetime import date
from psycopg2.extras import RealDictCursor

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def home():
    if 'usuario' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect ('/login')

    usuario_logado = session['usuario']

    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()

        query = """
            SELECT nomeclatura
            FROM usuarios
            WHERE nome = %s
        """
        cursor.execute(query, (usuario_logado,))
        resultado = cursor.fetchone()
        nomeclatura = resultado[0] if resultado else 'Usuário'
        session['nomeclatura'] = nomeclatura

    except Exception as e:
        print(f"Erro ao buscar nomeclatura: {e}")
        nomeclatura = 'Usuário'
    finally:
        if conexao:
            conexao.close()

    session['notificacoes'] = obter_notificacoes(usuario_logado)

    return render_template('home.html', nomeclatura=nomeclatura, notificacoes=session['notificacoes'])

@home_bp.route('/remover_notificacao', methods=['POST'])
def remover_notificacao():
    data = request.json

    if 'usuario' not in session:
        return jsonify({"success": False, "error": "Usuário não autenticado."}), 403

    print("JSON recebido:", data) 
    
    usuario_logado = session['usuario']

    if "id_not" in data:
        id_not = data["id_not"]

        try:
            conexao = criar_conexao()
            cursor = conexao.cursor()

            query = """
                UPDATE not_gerencia
                SET estado = 'inativa'
                WHERE id_not = %s
            """
            cursor.execute(query, (id_not))
            conexao.commit()

            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Notificação não encontrada."}), 404

            return jsonify({"success": True})

        except ValueError:
            return jsonify({"success": False, "error": "ID inválido."}), 400

        except Exception as e:
            print(f"Erro ao remover notificação: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

        finally:
            if 'conexao' in locals():
                conexao.close()

    return jsonify({"success": False, "error": "Dados inválidos."}), 400