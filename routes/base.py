from flask import Blueprint, render_template, request, session, flash, redirect, jsonify
from functions import criar_conexao
from datetime import date

base_bp = Blueprint('base', __name__)

@base_bp.route('/minhascobrancas', methods=['GET'])
def minhascobrancas():
    try:
        conexao = criar_conexao()
        cursor = conexao.cursor()
        data_hoje = date.today()
        usuario_logado = session['usuario']

        query_atendimentos = """
            SELECT nome_cliente, observacao
            FROM atendimentos 
            WHERE data_atendimento = %s
            AND usuario = %s
            ORDER BY data_atendimento ASC
        """
        
        cursor.execute(query_atendimentos, (data_hoje, usuario_logado))
        atendimentos = cursor.fetchall()

        return jsonify({"atendimentos": atendimentos})
    
    except Exception as e:
        print(f"Erro ao carregar atendimentos: {e}")
        return jsonify({"atendimentos": []})