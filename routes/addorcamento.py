from flask import Blueprint, render_template, request, redirect, url_for

addorcamento_bp = Blueprint('addorcamento', __name__, template_folder='templates')

@addorcamento_bp.route('/addorcamento', methods=['GET', 'POST'])
def add_orcamento():
    if request.method == 'POST':
        # Coleta os dados do formulário
        produtor = request.form['produtor']
        validade = request.form['validade']
        data = request.form['data']
        total = request.form['total']
        produtos = zip(request.form.getlist('produto[]'), 
                       request.form.getlist('quantidade[]'), 
                       request.form.getlist('preco[]'))

        # Salve os dados no banco de dados aqui (exemplo com SQLAlchemy ou outra abordagem)
        # Seu código para salvar os dados vai aqui

        # Após salvar, redireciona para a página de gerenciamento
        return redirect(url_for('gerencia.gerencia'))  # Ajuste para a rota correta

    # Caso seja um GET, renderiza o formulário para novo orçamento
    return render_template('addorcamento.html')

