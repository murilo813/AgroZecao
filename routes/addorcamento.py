from flask import Blueprint, render_template, request, redirect, url_for

addorcamento_bp = Blueprint('addorcamento', __name__, template_folder='templates')

@addorcamento_bp.route('/addorcamento', methods=['GET', 'POST'])
def add_orcamento():
    if request.method == 'POST':
        produtor = request.form['produtor']
        validade = request.form['validade']
        data = request.form['data']
        total = request.form['total']
        produtos = zip(request.form.getlist('produto[]'), 
                       request.form.getlist('quantidade[]'), 
                       request.form.getlist('preco[]'))


        return redirect(url_for('gerencia.gerencia'))  

    return render_template('addorcamento.html')

