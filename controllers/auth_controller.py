from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from models.usuario import Usuario
from models.repositorio import RepositorioUsuarios
from utils.validacoes import validar_formato_cpf, sanitizar_cpf

# Blueprint agrupa rotas relacionadas à autenticação
auth_bp = Blueprint("auth", __name__)

repo = RepositorioUsuarios()


# ── Página inicial ────────────────────────────────────────────────────────────

@auth_bp.route("/")
def home():
    return render_template("index.html")


# ── Cadastro ──────────────────────────────────────────────────────────────────

@auth_bp.route("/cadastro-usuario", methods=["GET", "POST"])
def cadastrar_usuario():
    if request.method == "GET":
        return render_template("cadastro-usuario.html")

    # 1. Coleta dos dados do formulário
    nome   = request.form.get("nome", "").strip()
    cpf    = request.form.get("cpf", "").strip()
    email  = request.form.get("email", "").strip()
    senha  = request.form.get("senha", "")
    perfil = request.form.get("perfil", "comum")

    # 2. Validação de idade
    try:
        idade = int(request.form.get("idade", 0))
    except ValueError:
        flash("Idade inválida.", "erro")
        return redirect(url_for("auth.cadastrar_usuario"))

    if idade < 18:
        flash("Cadastro permitido apenas para maiores de 18 anos.", "erro")
        return redirect(url_for("auth.cadastrar_usuario"))

    # 3. Validação de formato do CPF
    if not validar_formato_cpf(cpf):
        flash("CPF inválido. Use o formato 000.000.000-00.", "erro")
        return redirect(url_for("auth.cadastrar_usuario"))

    # 4. Unicidade do CPF
    if repo.cpf_existe(cpf):
        flash("CPF já cadastrado no sistema.", "erro")
        return redirect(url_for("auth.cadastrar_usuario"))

    # 5. Criação do objeto e persistência
    senha_hash = generate_password_hash(senha)
    cpf_salvo  = sanitizar_cpf(cpf)

    novo_usuario = Usuario(nome, cpf_salvo, email, idade, senha_hash, perfil)

    if repo.salvar(novo_usuario):
        flash("Usuário cadastrado com sucesso.", "sucesso")
        return redirect(url_for("auth.login"))
    else:
        flash("Não foi possível cadastrar o usuário.", "erro")
        return redirect(url_for("auth.cadastrar_usuario"))


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf_digitado = sanitizar_cpf(request.form.get("cpf", ""))
        senha        = request.form.get("senha", "")

        usuario = repo.buscar_por_cpf(cpf_digitado)

        if usuario and check_password_hash(usuario.senha, senha):
            session["usuario_id"]     = usuario.id
            session["usuario_nome"]   = usuario.nome
            session["usuario_perfil"] = usuario.perfil
            flash(f"Bem-vindo, {usuario.nome}!", "sucesso")
            return redirect('/dashboard')

        flash("CPF ou senha inválidos.", "erro")

    return render_template("login.html")


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "sucesso")
    return redirect(url_for("auth.login"))