from flask import Flask, render_template, session
from controllers.auth_controller import auth_bp
from controllers.usuario_controller import usuario_bp
from models.repositorio import RepositorioUsuarios

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

# Registro dos Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(usuario_bp)

# Rota do Dashboard (Página Inicial após login)
@app.route('/dashboard')
def dashboard():
    repo = RepositorioUsuarios()
    usuarios = repo.listar()
    total_u = len(usuarios)
    
    # Dados fictícios para os chamados (serão substituídos pela API no futuro)
    return render_template('dashboard.html', 
                           total_usuarios=total_u,
                           total_chamados_abertos=15,
                           total_chamados_resolvidos=42)

# Rotas do Visual do Helpdesk
@app.route('/chamados')
def chamados_lista():
    return render_template('chamados_lista.html')

@app.route('/chamados/novo')
def chamado_novo():
    return render_template('chamados_novo.html')

@app.route('/chamados/<int:id>')
def chamado_detalhes(id):
    # O ID pode ser usado posteriormente para buscar os dados via API
    return render_template('chamados_detalhes.html')

if __name__ == "__main__":
    app.run(debug=True)