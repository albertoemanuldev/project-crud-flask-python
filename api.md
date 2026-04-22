# API Helpdesk — Chamados

Documentação completa para implementação do módulo de Chamados/Helpdesk sobre o sistema MVC de gerenciamento de usuários.

---

## Visão geral

O módulo de Helpdesk adiciona um domínio de **chamados de suporte** ao sistema existente. Usuários comuns abrem chamados e acompanham o atendimento. Administradores recebem, atribuem, respondem e encerram os chamados.

O diferencial didático deste domínio é a **máquina de estados** — um chamado percorre um ciclo de vida bem definido, e a API precisa enforçar quais transições são permitidas, por quem, e em qual ordem.

---

## Integração com o sistema MVC existente

O módulo reutiliza diretamente:

- A tabela `usuarios` (cpf, nome, perfil)
- Os perfis `admin` e `comum`
- A autenticação JWT (a ser implementada no Bloco 3)
- O repositório e padrão de classes do projeto

Nenhuma alteração é necessária nas tabelas ou controllers existentes. O Helpdesk é adicionado como um novo **Blueprint** (`api/v1/chamados`) sobre a mesma base.

---

## Estrutura de pastas proposta

```
login_mvc/
├── app.py
├── controllers/
│   ├── auth_controller.py
│   └── usuario_controller.py
├── models/
│   ├── usuario.py
│   ├── repositorio.py
│   ├── chamado.py             ← novo
│   └── chamado_repositorio.py ← novo
├── api/
│   ├── __init__.py            ← novo
│   ├── v1/
│   │   ├── __init__.py        ← novo
│   │   ├── auth.py            ← novo (JWT login)
│   │   ├── usuarios.py        ← novo (CRUD via API)
│   │   └── chamados.py        ← novo (este módulo)
└── utils/
    ├── validacoes.py
    └── transicoes.py          ← novo (máquina de estados)
```

---

## Banco de dados

### Tabelas novas

As tabelas abaixo se juntam à tabela `usuarios` já existente. As chaves estrangeiras referenciam o campo `cpf` da tabela `usuarios`.

```sql
CREATE TABLE chamados (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    titulo          VARCHAR(120)  NOT NULL,
    descricao       TEXT          NOT NULL,
    categoria       ENUM('infra', 'sistema', 'acesso', 'outro') NOT NULL,
    prioridade      ENUM('baixa', 'media', 'alta', 'critica')   NOT NULL,
    status          ENUM('aberto', 'em_atendimento', 'aguardando_usuario', 'resolvido', 'fechado')
                    NOT NULL DEFAULT 'aberto',
    cpf_solicitante VARCHAR(11)   NOT NULL,
    cpf_responsavel VARCHAR(11)   NULL,
    criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cpf_solicitante) REFERENCES usuarios(cpf),
    FOREIGN KEY (cpf_responsavel) REFERENCES usuarios(cpf)
);

CREATE TABLE comentarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    chamado_id  INT           NOT NULL,
    cpf_autor   VARCHAR(11)   NOT NULL,
    conteudo    TEXT          NOT NULL,
    interno     BOOLEAN       NOT NULL DEFAULT FALSE,
    criado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chamado_id) REFERENCES chamados(id),
    FOREIGN KEY (cpf_autor)  REFERENCES usuarios(cpf)
);

CREATE TABLE historico_status (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    chamado_id      INT           NOT NULL,
    cpf_autor       VARCHAR(11)   NOT NULL,
    status_anterior ENUM('aberto', 'em_atendimento', 'aguardando_usuario', 'resolvido', 'fechado') NOT NULL,
    status_novo     ENUM('aberto', 'em_atendimento', 'aguardando_usuario', 'resolvido', 'fechado') NOT NULL,
    motivo          TEXT          NULL,
    criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chamado_id) REFERENCES chamados(id),
    FOREIGN KEY (cpf_autor)  REFERENCES usuarios(cpf)
);
```

### Relacionamentos

| Relação | Cardinalidade | Descrição |
|---|---|---|
| `usuarios` → `chamados` | 1 para N | Um usuário abre muitos chamados (`cpf_solicitante`) |
| `usuarios` → `chamados` | 1 para N | Um admin atende muitos chamados (`cpf_responsavel`) |
| `chamados` → `comentarios` | 1 para N | Um chamado tem muitos comentários |
| `chamados` → `historico_status` | 1 para N | Um chamado tem muitos registros de histórico |
| `usuarios` → `comentarios` | 1 para N | Um usuário escreve muitos comentários |
| `usuarios` → `historico_status` | 1 para N | Um usuário executa muitas transições |

---

## Máquina de estados

### Os 5 estados

| Status | Descrição |
|---|---|
| `aberto` | Chamado recém-criado, aguardando atribuição |
| `em_atendimento` | Um admin assumiu e está trabalhando na solução |
| `aguardando_usuario` | Admin pediu informações adicionais ao solicitante |
| `resolvido` | Admin aplicou a solução, aguardando confirmação |
| `fechado` | Encerrado definitivamente — nenhuma ação é mais possível |

### Matriz de transições permitidas

A célula indica **quem** pode executar a transição. `403` significa transição proibida.

| De \ Para | `em_atendimento` | `aguardando_usuario` | `resolvido` | `fechado` |
|---|---|---|---|---|
| `aberto` | admin | admin | 403 | 403 |
| `em_atendimento` | — | admin | admin | 403 |
| `aguardando_usuario` | qualquer | — | admin | 403 |
| `resolvido` | admin (reabrir) | 403 | — | usuário solicitante |
| `fechado` | 403 | 403 | 403 | — |

> **Regra de ouro:** o estado `fechado` é terminal. Nenhuma transição sai dele.

### Implementação da máquina de estados em Python

```python
# utils/transicoes.py

TRANSICOES_PERMITIDAS = {
    'aberto': {
        'em_atendimento':    ['admin'],
        'aguardando_usuario': ['admin'],
    },
    'em_atendimento': {
        'aguardando_usuario': ['admin'],
        'resolvido':          ['admin'],
    },
    'aguardando_usuario': {
        'em_atendimento': ['admin', 'comum'],
        'resolvido':      ['admin'],
    },
    'resolvido': {
        'em_atendimento': ['admin'],   # reabrir
        'fechado':        ['comum'],   # solicitante confirma
    },
    'fechado': {}                      # terminal — sem saídas
}

def validar_transicao(status_atual, status_novo, perfil_usuario):
    """
    Retorna True se a transição for permitida para o perfil informado.
    Lança ValueError com mensagem descritiva caso contrário.
    """
    transicoes = TRANSICOES_PERMITIDAS.get(status_atual, {})

    if status_novo not in transicoes:
        raise ValueError(
            f"Transição de '{status_atual}' para '{status_novo}' não é permitida."
        )

    perfis_permitidos = transicoes[status_novo]
    if perfil_usuario not in perfis_permitidos:
        raise PermissionError(
            f"Perfil '{perfil_usuario}' não pode executar essa transição."
        )

    return True
```

---

## Endpoints da API

### Autenticação

Todos os endpoints abaixo exigem o header:

```
Authorization: Bearer <token_jwt>
```

O token é obtido em `POST /api/v1/auth/login`.

---

### Chamados

#### `POST /api/v1/chamados`

Abre um novo chamado.

**Acesso:** qualquer usuário autenticado

**Body (JSON):**
```json
{
  "titulo": "Não consigo acessar o sistema",
  "descricao": "Desde ontem meu login não funciona...",
  "categoria": "acesso",
  "prioridade": "alta"
}
```

**Regras:**
- `cpf_solicitante` é extraído do JWT — nunca do body
- `status` é sempre `aberto` na criação, ignorar se enviado no body
- `cpf_responsavel` começa como `null`
- Campos obrigatórios: `titulo`, `descricao`, `categoria`, `prioridade`

**Resposta de sucesso:** `201 Created`
```json
{
  "id": 42,
  "titulo": "Não consigo acessar o sistema",
  "status": "aberto",
  "prioridade": "alta",
  "categoria": "acesso",
  "cpf_solicitante": "11111111111",
  "cpf_responsavel": null,
  "criado_em": "2025-08-10T14:30:00"
}
```

---

#### `GET /api/v1/chamados`

Lista chamados.

**Acesso:** qualquer usuário autenticado

**Comportamento por perfil:**
- `comum` — retorna apenas os chamados onde `cpf_solicitante = cpf_do_jwt`
- `admin` — retorna todos os chamados

**Query params disponíveis (apenas admin):**

| Parâmetro | Exemplo | Descrição |
|---|---|---|
| `status` | `?status=aberto` | Filtra por status |
| `prioridade` | `?prioridade=critica` | Filtra por prioridade |
| `responsavel` | `?responsavel=11111111111` | Filtra por admin responsável |
| `page` | `?page=2` | Paginação (padrão: 1) |
| `per_page` | `?per_page=20` | Itens por página (padrão: 10) |

**Resposta de sucesso:** `200 OK`
```json
{
  "data": [ { "id": 42, "titulo": "...", "status": "aberto" } ],
  "total": 1,
  "page": 1,
  "per_page": 10
}
```

---

#### `GET /api/v1/chamados/<id>`

Retorna um chamado específico com seus comentários.

**Acesso:** dono do chamado ou admin

**Regras:**
- Usuário comum que não é o solicitante recebe `403`
- Comentários com `interno: true` são omitidos para usuários comuns

**Resposta de sucesso:** `200 OK`
```json
{
  "id": 42,
  "titulo": "Não consigo acessar o sistema",
  "descricao": "Desde ontem...",
  "status": "em_atendimento",
  "prioridade": "alta",
  "categoria": "acesso",
  "cpf_solicitante": "11111111111",
  "cpf_responsavel": "22222222222",
  "criado_em": "2025-08-10T14:30:00",
  "atualizado_em": "2025-08-10T15:00:00",
  "comentarios": [
    {
      "id": 1,
      "cpf_autor": "22222222222",
      "conteudo": "Estamos verificando o problema.",
      "interno": false,
      "criado_em": "2025-08-10T15:00:00"
    }
  ]
}
```

---

#### `PATCH /api/v1/chamados/<id>/status`

Muda o status de um chamado.

**Acesso:** depende da transição (ver matriz acima)

**Body (JSON):**
```json
{
  "status_novo": "em_atendimento",
  "motivo": "Assumindo o chamado para investigação."
}
```

**Regras:**
- Validar a transição via `validar_transicao()` antes de qualquer UPDATE
- Registrar automaticamente um row em `historico_status`
- Se `status_novo = 'em_atendimento'` e `cpf_responsavel` ainda é `null`, atribuir ao admin que fez a requisição
- `motivo` é opcional mas recomendado

**Respostas:**

| Situação | Código |
|---|---|
| Transição executada com sucesso | `200 OK` |
| Transição inválida (ex: fechado → aberto) | `422 Unprocessable Entity` |
| Perfil sem permissão para essa transição | `403 Forbidden` |
| Chamado não encontrado | `404 Not Found` |

---

#### `PATCH /api/v1/chamados/<id>/responsavel`

Atribui ou reatribui o admin responsável.

**Acesso:** somente `admin`

**Body (JSON):**
```json
{
  "cpf_responsavel": "22222222222"
}
```

**Regras:**
- O CPF informado deve existir e ter perfil `admin`
- Chamado `fechado` não pode ter responsável alterado → `422`

**Resposta de sucesso:** `200 OK`

---

#### `DELETE /api/v1/chamados/<id>`

Exclui um chamado.

**Acesso:** somente `admin`

**Regras:**
- Só é possível excluir chamados com status `aberto`
- Chamados em andamento devem ser fechados primeiro → `422`

**Resposta de sucesso:** `204 No Content`

---

### Comentários

#### `POST /api/v1/chamados/<id>/comentarios`

Adiciona um comentário ao chamado.

**Acesso:** dono do chamado ou admin

**Body (JSON):**
```json
{
  "conteudo": "O problema persiste mesmo após reiniciar.",
  "interno": false
}
```

**Regras:**
- `cpf_autor` é extraído do JWT
- Usuário comum só pode comentar em seus próprios chamados → `403` caso contrário
- `interno: true` é permitido apenas para admins — se um comum enviar `true`, a API salva como `false` silenciosamente (ou retorna `403`, a critério do professor)
- Chamado com status `fechado` não aceita novos comentários → `422`

**Resposta de sucesso:** `201 Created`

---

#### `GET /api/v1/chamados/<id>/comentarios`

Lista todos os comentários de um chamado.

**Acesso:** dono do chamado ou admin

**Regras:**
- Usuário comum não recebe itens com `interno: true`
- Admin recebe todos

**Resposta de sucesso:** `200 OK`

---

### Histórico

#### `GET /api/v1/chamados/<id>/historico`

Retorna a trilha completa de mudanças de status.

**Acesso:** dono do chamado ou admin

**Resposta de sucesso:** `200 OK`
```json
[
  {
    "id": 1,
    "status_anterior": "aberto",
    "status_novo": "em_atendimento",
    "cpf_autor": "22222222222",
    "motivo": "Assumindo o chamado.",
    "criado_em": "2025-08-10T15:00:00"
  }
]
```

> O histórico é **somente leitura** — nenhum endpoint permite criar, editar ou deletar registros diretamente. Eles são gerados automaticamente pela camada de serviço a cada transição.

---

## Resumo dos endpoints

| Método | Rota | Descrição | Perfil |
|---|---|---|---|
| `POST` | `/api/v1/chamados` | Abrir chamado | comum + admin |
| `GET` | `/api/v1/chamados` | Listar chamados | comum + admin |
| `GET` | `/api/v1/chamados/<id>` | Detalhar chamado | dono + admin |
| `PATCH` | `/api/v1/chamados/<id>/status` | Mudar status | depende da transição |
| `PATCH` | `/api/v1/chamados/<id>/responsavel` | Atribuir responsável | admin |
| `DELETE` | `/api/v1/chamados/<id>` | Excluir chamado | admin |
| `POST` | `/api/v1/chamados/<id>/comentarios` | Comentar | dono + admin |
| `GET` | `/api/v1/chamados/<id>/comentarios` | Listar comentários | dono + admin |
| `GET` | `/api/v1/chamados/<id>/historico` | Ver histórico | dono + admin |

---

## Padrão de respostas de erro

Todos os erros seguem o mesmo envelope:

```json
{
  "erro": "Transição de 'fechado' para 'aberto' não é permitida.",
  "codigo": 422
}
```

### Códigos utilizados no módulo

| Código | Quando usar |
|---|---|
| `400 Bad Request` | Campo obrigatório ausente ou formato inválido |
| `401 Unauthorized` | Token JWT ausente ou expirado |
| `403 Forbidden` | Usuário autenticado mas sem permissão para a ação |
| `404 Not Found` | Chamado ou comentário não encontrado |
| `422 Unprocessable Entity` | Transição de status inválida ou regra de negócio violada |

---

## Regras de negócio consolidadas

### Criação

1. `cpf_solicitante` vem sempre do JWT (`get_jwt_identity()`), nunca do body
2. Status inicial é sempre `aberto`, independente do payload recebido
3. `cpf_responsavel` começa como `null`
4. Campos obrigatórios: `titulo`, `descricao`, `categoria`, `prioridade`

### Visibilidade

5. Usuário comum vê somente seus próprios chamados
6. Admin vê todos os chamados e pode filtrar por qualquer campo
7. Comentários `interno: true` são invisíveis para usuários comuns

### Transições de status

8. Toda transição é validada pela função `validar_transicao()` antes do UPDATE
9. Toda transição bem-sucedida gera um registro automático em `historico_status`
10. O estado `fechado` é terminal — nenhuma transição pode partir dele
11. Reabrir um chamado (`resolvido → em_atendimento`) só é permitido para admins

### Integridade

12. Registros em `historico_status` são imutáveis — nunca DELETE ou UPDATE nessa tabela
13. Chamados `fechados` não aceitam novos comentários
14. Usuário comum só comenta em chamados onde é o solicitante
15. Só é possível excluir chamados com status `aberto`

---

## Esqueleto de implementação

### Modelo `Chamado`

```python
# models/chamado.py

class Chamado:
    def __init__(self, id, titulo, descricao, categoria, prioridade,
                 status, cpf_solicitante, cpf_responsavel,
                 criado_em, atualizado_em):
        self.id              = id
        self.titulo          = titulo
        self.descricao       = descricao
        self.categoria       = categoria
        self.prioridade      = prioridade
        self.status          = status
        self.cpf_solicitante = cpf_solicitante
        self.cpf_responsavel = cpf_responsavel
        self.criado_em       = criado_em
        self.atualizado_em   = atualizado_em

    def to_dict(self):
        return {
            'id':               self.id,
            'titulo':           self.titulo,
            'descricao':        self.descricao,
            'categoria':        self.categoria,
            'prioridade':       self.prioridade,
            'status':           self.status,
            'cpf_solicitante':  self.cpf_solicitante,
            'cpf_responsavel':  self.cpf_responsavel,
            'criado_em':        str(self.criado_em),
            'atualizado_em':    str(self.atualizado_em),
        }
```

### Blueprint da API de chamados

```python
# api/v1/chamados.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.chamado_repositorio import ChamadoRepositorio
from utils.transicoes import validar_transicao

chamados_bp = Blueprint('chamados', __name__, url_prefix='/api/v1/chamados')
repo = ChamadoRepositorio()


@chamados_bp.route('', methods=['POST'])
@jwt_required()
def criar_chamado():
    cpf_solicitante = get_jwt_identity()
    dados = request.get_json()

    campos_obrigatorios = ['titulo', 'descricao', 'categoria', 'prioridade']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({'erro': f'Campo obrigatório ausente: {campo}', 'codigo': 400}), 400

    chamado = repo.criar(
        titulo          = dados['titulo'],
        descricao       = dados['descricao'],
        categoria       = dados['categoria'],
        prioridade      = dados['prioridade'],
        cpf_solicitante = cpf_solicitante,
    )
    return jsonify(chamado.to_dict()), 201


@chamados_bp.route('', methods=['GET'])
@jwt_required()
def listar_chamados():
    cpf     = get_jwt_identity()
    claims  = get_jwt()
    perfil  = claims.get('perfil')

    filtros = {}
    if perfil != 'admin':
        filtros['cpf_solicitante'] = cpf
    else:
        filtros['status']      = request.args.get('status')
        filtros['prioridade']  = request.args.get('prioridade')
        filtros['responsavel'] = request.args.get('responsavel')

    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    resultado = repo.listar(filtros, page, per_page)
    return jsonify(resultado), 200


@chamados_bp.route('/<int:id>/status', methods=['PATCH'])
@jwt_required()
def mudar_status(id):
    cpf    = get_jwt_identity()
    claims = get_jwt()
    perfil = claims.get('perfil')

    chamado = repo.buscar_por_id(id)
    if not chamado:
        return jsonify({'erro': 'Chamado não encontrado', 'codigo': 404}), 404

    dados      = request.get_json()
    status_novo = dados.get('status_novo')
    motivo      = dados.get('motivo')

    try:
        validar_transicao(chamado.status, status_novo, perfil)
    except ValueError as e:
        return jsonify({'erro': str(e), 'codigo': 422}), 422
    except PermissionError as e:
        return jsonify({'erro': str(e), 'codigo': 403}), 403

    repo.atualizar_status(id, status_novo, cpf, motivo)
    return jsonify({'status': status_novo}), 200
```

### Registro no `app.py`

```python
# app.py — adicionar após a criação do app Flask

from api.v1.chamados import chamados_bp
from api.v1.auth     import auth_bp

app.register_blueprint(chamados_bp)
app.register_blueprint(auth_bp)
```

---

## Sugestões de evolução

Funcionalidades que podem ser adicionadas após a implementação básica:

1. **Anexos** — tabela `anexos` ligada a `chamados`, upload via `multipart/form-data`
2. **Notificações** — endpoint `GET /api/v1/notificacoes` com chamados atualizados desde o último acesso
3. **SLA** — campo `prazo_resolucao` em `chamados`, calculado com base na prioridade
4. **Busca textual** — `GET /api/v1/chamados?q=palavra` fazendo `LIKE` em `titulo` e `descricao`
5. **Dashboard admin** — `GET /api/v1/relatorios/chamados` retornando contagens por status e prioridade

---

*Documento gerado como material didático para o módulo de Desenvolvimento de APIs — Curso Técnico de Programação Web.*