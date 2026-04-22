# Migração do Sistema de Login MVC de JSON para MySQL

Este documento fornece um guia passo a passo para migrar o sistema de gerenciamento de usuários de um armazenamento baseado em JSON para um banco de dados MySQL. Esta migração faz parte da unidade curricular de banco de dados, permitindo aos alunos progredir no projeto e implementar um sistema de persistência mais robusto e escalável.

## Pré-requisitos

Antes de iniciar a migração, certifique-se de que você tem:

- Python 3.8 ou superior instalado
- MySQL Server instalado e em execução
- Acesso administrativo ao MySQL (para criar bancos de dados e usuários)
- Conhecimento básico de SQL

## Passo 1: Instalar e Configurar o MySQL

### 1.1 Instalar o MySQL Server

Se ainda não tiver o MySQL instalado:

**Windows:**
- Baixe o MySQL Installer do site oficial: https://dev.mysql.com/downloads/installer/
- Execute o instalador e siga as instruções
- Durante a instalação, anote a senha do usuário root: admin



### 1.2 Verificar a Instalação

Abra o terminal e execute:
```bash
mysql --version
```

Deve mostrar algo como: `mysql Ver 8.0.XX for ...`

### 1.3 Acessar o MySQL como Root

```bash
mysql -u root -p
```

Digite a senha quando solicitada.

## Passo 2: Instalar as Dependências Python

### 2.1 Instalar o Conector MySQL para Python

No terminal, navegue até o diretório do projeto e execute:

```bash
pip install mysql-connector-python
```

### 2.2 Verificar a Instalação

```python
python -c "import mysql.connector; print('MySQL connector instalado com sucesso!')"
```

### 2.3 Criar requirements.txt (Opcional mas Recomendado)

Crie um arquivo `requirements.txt` na raiz do projeto com o conteúdo:

```
Flask==2.3.3
mysql-connector-python==8.1.0
```

Instale todas as dependências com:
```bash
pip install -r requirements.txt
```

## Passo 3: Criar o Banco de Dados e a Tabela

### 3.1 Criar o Banco de Dados

No MySQL (acessado via terminal):

```sql
CREATE DATABASE login_mvc_db;
USE login_mvc_db;
```

### 3.2 Criar a Tabela de Usuários

```sql
CREATE TABLE usuarios (
    id VARCHAR(36) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    idade INT NOT NULL,
    senha TEXT NOT NULL,
    perfil VARCHAR(20) DEFAULT 'comum'
);
```

### 3.3 Criar um Usuário para a Aplicação (Opcional mas Recomendado)

```sql
CREATE USER 'login_app'@'localhost' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON login_mvc_db.* TO 'login_app'@'localhost';
FLUSH PRIVILEGES;
```

Substitua `'sua_senha_segura'` por uma senha forte.

## Passo 4: Modificar o Código da Aplicação

### 4.1 Atualizar o Modelo Usuario (models/usuario.py)

O modelo `Usuario` não precisa de mudanças significativas, pois já tem métodos `to_dict()` e `from_dict()` que facilitam a conversão. No entanto, podemos adicionar validações adicionais se necessário.

### 4.2 Modificar o Repositório (models/repositorio.py)

Esta é a parte principal da migração. Precisamos substituir o acesso ao arquivo JSON por consultas ao MySQL.

**Conteúdo atualizado para `models/repositorio.py`:**

```python
import mysql.connector
from mysql.connector import Error
from models.usuario import Usuario
from utils.validacoes import sanitizar_cpf


class RepositorioUsuarios:
    """
    Responsabilidade: toda leitura e escrita de usuários no banco MySQL.
    O restante da aplicação não precisa saber que os dados estão em um banco.
    """

    def __init__(self):
        self.connection_config = {
            'host': 'localhost',
            'user': 'login_app',  # ou 'root' se não criou usuário específico
            'password': 'sua_senha_segura',  # senha do usuário MySQL
            'database': 'login_mvc_db'
        }

    def _get_connection(self):
        """Retorna uma conexão com o banco de dados."""
        try:
            connection = mysql.connector.connect(**self.connection_config)
            return connection
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            return None

    # ── Leitura ───────────────────────────────────────────────────

    def listar(self) -> list[Usuario]:
        """Retorna todos os usuários como lista de objetos Usuario."""
        connection = self._get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios")
            rows = cursor.fetchall()
            return [Usuario.from_dict(row) for row in rows]
        except Error as e:
            print(f"Erro ao listar usuários: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def buscar_por_cpf(self, cpf: str) -> Usuario | None:
        """Busca um usuário pelo CPF (ignora formatação)."""
        connection = self._get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            cpf_limpo = sanitizar_cpf(cpf)
            cursor.execute("SELECT * FROM usuarios WHERE cpf = %s", (cpf_limpo,))
            row = cursor.fetchone()
            return Usuario.from_dict(row) if row else None
        except Error as e:
            print(f"Erro ao buscar usuário por CPF: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def cpf_existe(self, cpf: str) -> bool:
        """Retorna True se o CPF já está cadastrado."""
        return self.buscar_por_cpf(cpf) is not None

    # ── Escrita ───────────────────────────────────────────────────

    def salvar(self, usuario: Usuario) -> bool:
        """Adiciona um novo usuário ao banco de dados."""
        connection = self._get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            sql = """INSERT INTO usuarios (id, nome, cpf, email, idade, senha, perfil) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            valores = (usuario.id, usuario.nome, usuario.cpf, usuario.email, 
                      usuario.idade, usuario.senha, usuario.perfil)
            cursor.execute(sql, valores)
            connection.commit()
            return True
        except Error as e:
            print(f"Erro ao salvar usuário: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def atualizar(self, usuario_atualizado: Usuario) -> bool:
        """
        Atualiza os dados de um usuário existente pelo CPF.
        Retorna False se o usuário não for encontrado.
        """
        connection = self._get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            sql = """UPDATE usuarios SET nome=%s, email=%s, idade=%s, senha=%s, perfil=%s 
                     WHERE cpf=%s"""
            valores = (usuario_atualizado.nome, usuario_atualizado.email, 
                      usuario_atualizado.idade, usuario_atualizado.senha, 
                      usuario_atualizado.perfil, usuario_atualizado.cpf)
            cursor.execute(sql, valores)
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Erro ao atualizar usuário: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def deletar(self, cpf: str) -> bool:
        """Remove o usuário com o CPF informado."""
        connection = self._get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cpf_limpo = sanitizar_cpf(cpf)
            cursor.execute("DELETE FROM usuarios WHERE cpf = %s", (cpf_limpo,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Erro ao deletar usuário: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
```

**Importante:** Substitua `'sua_senha_segura'` pela senha real do usuário MySQL criado.

### 4.3 Atualizar o app.py (Opcional)

Se desejar, você pode adicionar configurações do banco no `app.py`, mas como o repositório gerencia a conexão, não é estritamente necessário.

## Passo 5: Migrar os Dados Existentes

### 5.1 Criar um Script de Migração

Crie um arquivo `migrar_dados.py` na raiz do projeto:

```python
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
```

### 5.2 Executar a Migração

```bash
python migrar_dados.py
```

### 5.3 Verificar a Migração

Após a migração, você pode verificar se os dados foram transferidos corretamente:

```sql
USE login_mvc_db;
SELECT * FROM usuarios;
```

## Passo 6: Testar a Aplicação

### 6.1 Executar o Sistema

```bash
python app.py
```

### 6.2 Testar as Funcionalidades

- Acesse a aplicação no navegador
- Teste o login com o usuário admin
- Teste o cadastro de novos usuários
- Teste a edição e exclusão de usuários
- Verifique se os dados persistem após reiniciar a aplicação

## Passo 7: Limpeza (Opcional)

Após confirmar que tudo funciona corretamente:

1. Faça backup do arquivo `usuarios.json`
2. Remova ou renomeie o arquivo `usuarios.json` (já que não é mais usado)
3. Remova o script `migrar_dados.py` se não for mais necessário

## Troubleshooting

### Erro de Conexão ao MySQL

- Verifique se o MySQL Server está em execução
- Confirme as credenciais no `repositorio.py`
- Verifique se o usuário tem permissões no banco

### Erro de Codificação

Se houver problemas com caracteres especiais (acentos), adicione ao `connection_config`:

```python
'charset': 'utf8mb4',
'collation': 'utf8mb4_unicode_ci'
```

### Erro de CPF Duplicado

Durante a migração, se houver CPFs duplicados no JSON, apenas o primeiro será migrado. Limpe os dados antes da migração se necessário.

## Próximos Passos

Com o MySQL implementado, você pode:

1. Adicionar índices para melhorar performance
2. Implementar transações para operações complexas
3. Adicionar logs de auditoria
4. Implementar paginação para listagem de usuários
5. Adicionar relacionamentos (ex: histórico de logins)

## Referências

- [Documentação Oficial do MySQL](https://dev.mysql.com/doc/)
- [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)
- [Flask Documentation](https://flask.palletsprojects.com/)