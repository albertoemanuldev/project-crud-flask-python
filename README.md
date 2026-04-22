# Sistema de Login MVC - Gerenciamento de Usuários

Um sistema web completo para gerenciamento de usuários desenvolvido em Python com Flask, seguindo a arquitetura MVC (Model-View-Controller). O sistema permite cadastro, login, edição e exclusão de usuários, com controle de permissões baseado em perfis (admin/comum).

## 📋 Visão Geral

Este projeto foi desenvolvido como material didático para demonstrar conceitos fundamentais de desenvolvimento web, incluindo:

- **Arquitetura MVC**: Separação clara entre Model, View e Controller
- **Autenticação e Autorização**: Sistema de login com sessões e controle de acesso
- **Validação de Dados**: Validações de CPF, idade e outros campos
- **Persistência de Dados**: Inicialmente com JSON, com migração para MySQL
- **Interface Web**: Templates HTML com CSS responsivo
- **APIs REST**: Endpoints JSON para integração

## 🚀 Funcionalidades

### Autenticação
- ✅ Cadastro de novos usuários
- ✅ Login com CPF e senha
- ✅ Logout seguro
- ✅ Validação de CPF no formato brasileiro
- ✅ Restrição de idade (maiores de 18 anos)

### Gerenciamento de Usuários
- ✅ Listagem de todos os usuários (com filtros e ordenação)
- ✅ Edição de perfil próprio ou de outros (admin)
- ✅ Exclusão de usuários (apenas admin)
- ✅ Busca por nome ou CPF
- ✅ Ordenação por idade

### Controle de Acesso
- ✅ Perfis de usuário: `admin` e `comum`
- ✅ Restrições baseadas em perfil
- ✅ Sessões seguras

### Persistência de Dados
- ✅ **Resiliência**: Sistema automaticamente usa MySQL se disponível, senão JSON
- ✅ **Migração**: Script automatizado para transferir dados
- ✅ **Fallback**: Operação contínua mesmo sem banco configurado

### APIs
- ✅ Endpoint JSON para listagem de usuários
- ✅ Estrutura preparada para expansão

## 🏗️ Arquitetura

### MVC (Model-View-Controller)

```
login_mvc/
├── app.py                 # Aplicação Flask principal
├── migrar_dados.py        # Script de migração JSON → MySQL
├── requirements.txt       # Dependências Python
├── .env.example          # Exemplo de variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── LICENSE               # Licença MIT
├── README.md             # Esta documentação
├── README_MIGRACAO_MYSQL.md  # Guia de migração para MySQL
├── usuarios.json         # Dados (JSON) - usado como fallback
├── controllers/          # Controladores (Lógica de aplicação)
│   ├── auth_controller.py    # Autenticação e cadastro
│   └── usuario_controller.py # Gestão de usuários
├── models/               # Modelos (Lógica de negócio)
│   ├── repositorio.py    # Repositório de dados (MySQL/JSON)
│   └── usuario.py        # Classe Usuario
├── static/               # Assets estáticos
│   ├── index.css
│   ├── login.css
│   ├── cadastro-usuario.css
│   ├── usuarios.css
│   └── editar.css
├── templates/            # Templates HTML
│   ├── index.html
│   ├── login.html
│   ├── cadastro-usuario.html
│   ├── usuarios.html
│   └── editar_usuario.html
└── utils/                # Utilitários
    └── validacoes.py     # Validações de CPF e dados
```

### Fluxo de Dados

1. **Requisição** → Controller
2. **Controller** → Repository (Model)
3. **Repository** → Banco de dados
4. **Controller** → Template (View)
5. **Template** → Resposta HTML

## 📦 Instalação e Configuração

### Pré-requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)

### 1. Clonagem do Repositório

```bash
git clone <url-do-repositorio>
cd login_mvc
```

### 2. Instalação das Dependências

```bash
pip install -r requirements.txt
```

### 3. Configuração do Banco de Dados

**Opção A: Usar JSON (padrão inicial)**
- Os dados são salvos em `usuarios.json`
- Não requer configuração adicional
- Sistema funciona imediatamente

**Opção B: Migrar para MySQL**
- Siga o guia em [README_MIGRACAO_MYSQL.md](README_MIGRACAO_MYSQL.md)
- Execute `python migrar_dados.py` para transferir dados existentes
- Sistema automaticamente detecta e usa MySQL se disponível
- Fallback automático para JSON se MySQL não estiver configurado

### 4. Execução

```bash
python app.py
```

Acesse: http://localhost:5000

**Nota**: O sistema funciona imediatamente com JSON. Para usar MySQL, configure o banco e execute a migração.

## 🔧 Configuração

### Usuário Admin Padrão

Após a instalação inicial, o sistema cria automaticamente um usuário admin:

- **CPF**: 111.111.111-11
- **Senha**: admin
- **Perfil**: admin

### Variáveis de Ambiente

O sistema suporta configuração via arquivo `.env`. Copie `.env.example` para `.env` e ajuste:

```env
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
MYSQL_HOST=localhost
MYSQL_USER=login_app
MYSQL_PASSWORD=sua-senha
MYSQL_DATABASE=login_mvc_db
```

### Variáveis de Ambiente (Opcional)

Crie um arquivo `.env` na raiz do projeto:

```env
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
MYSQL_HOST=localhost
MYSQL_USER=login_app
MYSQL_PASSWORD=sua-senha
MYSQL_DATABASE=login_mvc_db
```

## 📖 Uso

### Navegação Básica

1. **Página Inicial**: http://localhost:5000
2. **Login**: Clique em "Acessar Login"
3. **Cadastro**: Clique em "Realizar Cadastro"
4. **Dashboard**: Após login, visualize e gerencie usuários

### Funcionalidades por Perfil

#### Usuário Comum
- ✅ Visualizar lista de usuários
- ✅ Editar próprio perfil
- ✅ Logout

#### Administrador
- ✅ Todas as permissões do usuário comum
- ✅ Editar qualquer usuário
- ✅ Excluir usuários
- ✅ Acesso a APIs JSON

## 🔌 API Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página inicial |
| GET/POST | `/login` | Login de usuário |
| GET/POST | `/cadastro-usuario` | Cadastro de usuário |
| GET | `/logout` | Logout |

### Gestão de Usuários

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| GET | `/usuarios` | Listar usuários | ✅ |
| GET | `/usuarios/json` | Listar usuários (JSON) | ✅ |
| GET/POST | `/usuarios/editar/<cpf>` | Editar usuário | ✅ |
| POST | `/usuarios/deletar` | Excluir usuário | ✅ (Admin) |

### Parâmetros de Query

#### Listagem (`/usuarios`)
- `q`: Busca por nome ou CPF
- `ordem`: Ordenação por idade (`asc` ou `desc`)

Exemplo: `/usuarios?q=joao&ordem=asc`

## 🗃️ Modelo de Dados

### Usuário

```python
class Usuario:
    id: str          # UUID único
    nome: str        # Nome completo
    cpf: str         # CPF (formato limpo: 12345678901)
    email: str       # Email único
    idade: int       # Idade em anos
    senha: str       # Hash da senha
    perfil: str      # 'admin' ou 'comum'
```

### Validações

- **CPF**: Formato brasileiro (000.000.000-00)
- **Idade**: Mínimo 18 anos
- **Email**: Único no sistema
- **CPF**: Único no sistema
- **Senha**: Hash seguro com Werkzeug

## 🎨 Interface

### Páginas Principais

- **Index**: Página inicial com navegação
- **Login**: Formulário de autenticação
- **Cadastro**: Formulário de registro
- **Usuários**: Dashboard com lista e ações
- **Editar**: Formulário de edição de perfil

### Estilos

- Design responsivo
- Paleta de cores consistente
- Feedback visual (mensagens de sucesso/erro)
- Navegação intuitiva

## 🧪 Testes

### Testes Manuais

1. **Cadastro**: Tente cadastrar usuários válidos e inválidos
2. **Login**: Teste credenciais corretas e incorretas
3. **Permissões**: Verifique restrições por perfil
4. **CRUD**: Teste criação, leitura, atualização e exclusão

### Validações a Testar

- CPF com formato incorreto
- Idade menor que 18
- Email/CPF duplicados
- Campos obrigatórios vazios
- Acesso não autorizado

## 🔒 Segurança

### Medidas Implementadas

- **Hash de Senhas**: Uso de `werkzeug.security`
- **Sessões Seguras**: Controle de sessão Flask
- **Validação de Entrada**: Sanitização de CPF e validações
- **Controle de Acesso**: Verificação de permissões
- **Proteção CSRF**: Implícita nos formulários Flask

### Recomendações Adicionais

- Usar HTTPS em produção
- Configurar CORS se necessário
- Implementar rate limiting
- Logs de segurança

## 🚀 Próximos Passos

### Melhorias Sugeridas

1. **Banco de Dados**
   - ✅ Migração para MySQL (concluída)
   - Adicionar índices
   - Implementar transações

2. **Funcionalidades**
   - Recuperação de senha
   - Confirmação por email
   - Histórico de ações
   - Paginação

3. **Segurança**
   - Autenticação de dois fatores
   - Logs de auditoria
   - Validação avançada

4. **Interface**
   - Design responsivo aprimorado
   - Tema dark/light
   - Notificações em tempo real

5. **APIs**
   - Documentação OpenAPI/Swagger
   - Autenticação JWT
   - Rate limiting

## 📚 Referências

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/en/2.3.x/utils/#werkzeug.security)
- [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)
- [Guia de Migração MySQL](README_MIGRACAO_MYSQL.md)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)

## 📄 Arquivos de Documentação

- `README.md` - Documentação principal do projeto
- `README_MIGRACAO_MYSQL.md` - Guia detalhado de migração para MySQL
- `.env.example` - Exemplo de configuração de ambiente
- `requirements.txt` - Lista de dependências Python
- `LICENSE` - Licença do projeto

## 👥 Contribuição

Este é um projeto educacional. Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Desenvolvido como material didático para a unidade curricular de Desenvolvimento Web.**