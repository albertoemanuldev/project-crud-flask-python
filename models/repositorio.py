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
            'password': 'admin',  # senha do usuário MySQL
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