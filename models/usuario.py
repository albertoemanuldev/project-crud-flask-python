import uuid


class Usuario:
    """
    Representa um usuário do sistema.
    Responsabilidade: guardar os dados e expor comportamentos do usuário.
    """

    def __init__(self, nome: str, cpf: str, email: str, idade: int,
                 senha: str, perfil: str = "comum"):
        self.id     = str(uuid.uuid4())
        self.nome   = nome
        self.cpf    = cpf
        self.email  = email
        self.idade  = int(idade)
        self.senha  = senha
        self.perfil = perfil

    # ── Comportamentos ────────────────────────────────────────────

    def eh_maior_de_idade(self) -> bool:
        """Retorna True se o usuário tem 18 anos ou mais."""
        return self.idade >= 18

    def eh_admin(self) -> bool:
        """Retorna True se o perfil do usuário é admin."""
        return self.perfil == "admin"

    def pode_deletar(self) -> bool:
        """Apenas admins podem deletar outros usuários."""
        return self.eh_admin()

    # ── Serialização ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário (para salvar no JSON)."""
        return {
            "id":     self.id,
            "nome":   self.nome,
            "cpf":    self.cpf,
            "email":  self.email,
            "idade":  self.idade,
            "senha":  self.senha,
            "perfil": self.perfil,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Usuario":
        """
        Cria um objeto Usuario a partir de um dicionário.
        Usado ao carregar os dados do arquivo JSON.
        """
        usuario        = cls.__new__(cls)
        usuario.id     = dados.get("id", str(uuid.uuid4()))
        usuario.nome   = dados.get("nome", "")
        usuario.cpf    = dados.get("cpf", "")
        usuario.email  = dados.get("email", "")
        usuario.idade  = int(dados.get("idade", 0))
        usuario.senha  = dados.get("senha", "")
        usuario.perfil = dados.get("perfil", "comum")
        return usuario

    # ── Representação ─────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<Usuario nome={self.nome} cpf={self.cpf} perfil={self.perfil}>"