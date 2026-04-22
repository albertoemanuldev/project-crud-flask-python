import json

from models.repositorio import RepositorioUsuarios
from models.usuario import Usuario

def migrar_dados():
    """Migra os dados do JSON para o MySQL."""
    # Carregar dados do JSON
    try:
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            dados_json = json.load(f)
    except FileNotFoundError:
        print("Arquivo usuarios.json não encontrado.")
        return

    # Conectar ao repositório MySQL
    repo = RepositorioUsuarios()

    # Migrar cada usuário
    for dados_usuario in dados_json:
        usuario = Usuario.from_dict(dados_usuario)
        if repo.salvar(usuario):
            print(f"Usuário {usuario.nome} migrado com sucesso.")
        else:
            print(f"Erro ao migrar usuário {usuario.nome}.")

    print("Migração concluída!")

if __name__ == "__main__":
    migrar_dados()