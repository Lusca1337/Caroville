# Caroville

Plataforma de caronas para estudantes da Univille. Conecta alunos que **oferecem carona** com alunos que **precisam de transporte**, a partir de local de saída, destino, horário e número de vagas.

**Autores:** Lucas Felipe, Pedro Placidina
**Instituição:** Universidade da Região de Joinville - Univille

## Descrição do sistema

O Caroville é uma aplicação web em que o aluno entra com o e-mail institucional (`@univille.br`) e pode:

- **oferecer carona** (como motorista, com veículo cadastrado), sempre com o Campus Univille como saída ou destino;
- **buscar carona** por saída, destino e horário e **solicitar uma vaga**;
- **aceitar ou recusar** pedidos recebidos, e **cancelar** carona ou solicitação;
- acompanhar tudo em **Minhas caronas** e manter o **perfil** e o veículo.

O telefone do motorista e do passageiro e a placa do carro só aparecem depois que o pedido é aceito. Com modelo, cor e placa, o passageiro reconhece o carro no ponto de encontro.

## Objetivo do MVP

Entregar o fluxo completo de uma carona entre bairros de Joinville e o Campus Univille: cadastro, oferta, busca, solicitação, aceite ou recusa e cancelamento. Fica fora do escopo: pagamento ou rateio de custos, chat interno, mapa com rotas em tempo real e avaliações entre usuários.

## Tecnologias utilizadas

| Camada | Tecnologia |
|--------|------------|
| Frontend | React 18, React Router, Vite |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Banco de dados | PostgreSQL (acesso com psycopg 3) |
| Autenticação | JWT (PyJWT) e senhas com bcrypt |
| Testes | pytest e httpx |

## Estrutura do projeto

```
Caroville/
├── backend/
│   ├── app/            API (rotas, regras de negócio, validações)
│   ├── database/       schema.sql (tabelas) e seed.sql (dados de exemplo)
│   ├── tests/          testes automáticos (pytest)
│   └── requirements.txt
├── frontend/           aplicação React (veja frontend/README.md)
└── docs/               requisitos, ADRs, endpoints e testes
```

## Pré-requisitos

- **Python 3.13** (https://www.python.org)
- **Node.js 18 ou mais novo** (https://nodejs.org)
- **PostgreSQL** (https://www.postgresql.org), com o `psql` ou o pgAdmin
- Git

## Instalação

1. Baixe o projeto:
   ```
   git clone https://github.com/Lusca1337/Caroville.git
   cd Caroville
   ```
2. Crie o banco de dados chamado `caroville` (veja a seção "Banco de dados").
3. Instale o backend:
   ```
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
   No Linux ou macOS, ative com `source venv/bin/activate`. No PowerShell do Windows, se aparecer erro de scripts bloqueados, rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
4. Crie o arquivo `.env` (veja "Variáveis de ambiente").
5. Instale o frontend:
   ```
   cd ..\frontend
   npm install
   ```

## Variáveis de ambiente

O backend lê o arquivo `backend/.env`. Copie o modelo `backend/.env.example` para `backend/.env` e ajuste:

| Variável | Para que serve | Exemplo |
|----------|----------------|---------|
| `DATABASE_URL` | Endereço do PostgreSQL | `postgresql://postgres:SUA_SENHA@localhost:5432/caroville` |
| `SECRET_KEY` | Chave que assina os tokens de login; use um texto grande e aleatório | `troque-esta-chave-por-um-texto-grande-e-aleatorio` |
| `TOKEN_MINUTOS` | Quanto tempo o login dura, em minutos | `120` |

O frontend usa por padrão a API em `http://localhost:8000`. Para mudar, crie `frontend/.env` com `VITE_API_URL=<endereço>` (modelo em `frontend/.env.example`).

O arquivo `.env` guarda a senha do banco e **não deve ser enviado ao GitHub** (está no `.gitignore`).

## Banco de dados

O banco é o PostgreSQL, com o banco `caroville`. Os scripts ficam em `backend/database`:

- `schema.sql` cria as tabelas `usuario`, `veiculo`, `local`, `carona` e `solicitacao` (e **apaga** as existentes);
- `seed.sql` insere os dados de exemplo: 8 locais (Campus Univille e 7 bairros) e 3 usuários.

O modelo está no [DER](#modelagem-de-dados-der) abaixo.

**Com o psql** (na pasta `backend`):

```
psql -U postgres -c "CREATE DATABASE caroville;"
psql -U postgres -d caroville -f database/schema.sql
psql -U postgres -d caroville -f database/seed.sql
```

**Com o pgAdmin:** crie o banco `caroville`, clique com o botão direito nele > Query Tool, abra e execute primeiro o `schema.sql` e depois o `seed.sql`.

Usuários de exemplo (senha `senha1234`): `lucas@univille.br` (já tem veículo e duas caronas), `maria@univille.br` e `joao@univille.br`.

## Execução

Use dois terminais, com o banco já criado.

**Backend** (na pasta `backend`, com o ambiente virtual ativado):

```
python -m uvicorn app.main:app --reload
```

A API fica em http://localhost:8000 e a documentação interativa em http://localhost:8000/docs. Como o MVP não envia e-mail de verdade, o link de confirmação do cadastro aparece no terminal do backend e também na resposta do cadastro.

**Frontend** (na pasta `frontend`):

```
npm run dev
```

Abra http://localhost:5173. O backend só aceita chamadas vindas dessa porta.

## Como executar os testes

Os testes automáticos usam o banco configurado no `backend/.env`, com `schema.sql` e `seed.sql` já carregados. Eles criam os próprios usuários e caronas e apagam tudo no final. Na pasta `backend`, com o ambiente virtual ativado:

```
python -m pytest
```

Para ver o nome de cada teste: `python -m pytest -v`. O que cada arquivo cobre e o roteiro manual para testar as telas estão em [docs/testes.md](docs/testes.md).

## Link para os protótipos

Protótipos de tela no Figma: https://www.figma.com/design/SCf876FNOK081GMjxVszv8

## Documentação técnica (MVP)

| # | Documento | Conteúdo |
|---|-----------|----------|
| 1 | [Requisitos funcionais, histórias de usuário e regras de negócio](docs/01-requisitos-funcionais.md) | RF, histórias com critérios de aceite BDD, RN |
| 2 | [Requisitos não funcionais](docs/02-requisitos-nao-funcionais.md) | RNF mensuráveis |
| 3 | [Protótipos de tela no Figma](https://www.figma.com/design/SCf876FNOK081GMjxVszv8) | 8 telas navegáveis ligadas às histórias |
| 4 | [Registros de decisão de arquitetura (ADRs)](#decisões-de-arquitetura-adrs) | Decisões tecnológicas |
| 5 | [Modelagem de dados (DER)](#modelagem-de-dados-der) | DER e restrições |
| 6 | [Documentação dos endpoints da API](docs/api-endpoints.md) | Rotas, regras e códigos de erro |
| 7 | [Testes](docs/testes.md) | O que os testes cobrem e roteiro manual das telas |

## Decisões de arquitetura (ADRs)

| ADR | Decisão | Status |
|-----|---------|--------|
| [ADR-001](docs/ADR-001-frontend.md) | Frontend com React | Aceito |
| [ADR-002](docs/ADR-002-banco-de-dados.md) | Banco de dados PostgreSQL | Aceito |
| [ADR-003](docs/ADR-003-execucao-local.md) | Execução local, sem hospedagem, no MVP | Aceito |
| [ADR-004](docs/ADR-004-backend.md) | Backend com Python | Aceito |
| [ADR-005](docs/ADR-005-autenticacao.md) | Autenticação com e-mail institucional e JWT | Aceito |

## Visão geral da arquitetura

```mermaid
flowchart LR
  U["Estudante (celular ou computador)"] --> F["Aplicação web (frontend)"]
  F -->|"HTTP (HTTPS quando hospedado)"| B["API (backend)"]
  B --> D[("Banco de dados")]
  B --> E["Serviço de e-mail (simulado no MVP)"]
```

## Escopo do MVP

Cadastro e login com e-mail institucional, oferta de carona, busca por saída/destino/horário, solicitação, aceite ou recusa, cancelamento e perfil com veículo.

Fora do escopo do MVP: pagamento ou rateio de custos, chat interno, mapa com rotas em tempo real e avaliações entre usuários.

## Modelagem de dados (DER)

```mermaid
erDiagram
  USUARIO ||--o{ VEICULO : possui
  USUARIO ||--o{ CARONA : oferece
  VEICULO ||--o{ CARONA : "usado em"
  LOCAL ||--o{ CARONA : origem
  LOCAL ||--o{ CARONA : destino
  CARONA ||--o{ SOLICITACAO : recebe
  USUARIO ||--o{ SOLICITACAO : faz

  USUARIO {
    int id PK
    string nome
    string email UK
    string senha_hash
    string curso
    string telefone
    boolean email_verificado
    datetime criado_em
  }
  VEICULO {
    int id PK
    int usuario_id FK
    string modelo
    string cor
    string placa UK
    int lugares
  }
  LOCAL {
    int id PK
    string nome UK
    string tipo "BAIRRO ou CAMPUS"
  }
  CARONA {
    int id PK
    int motorista_id FK
    int veiculo_id FK
    int origem_id FK
    int destino_id FK
    datetime saida_em
    int vagas_total
    int vagas_disponiveis
    string ponto_encontro
    string observacoes
    string status "ABERTA, LOTADA, CANCELADA, CONCLUIDA"
    datetime criado_em
  }
  SOLICITACAO {
    int id PK
    int carona_id FK
    int passageiro_id FK
    string status "PENDENTE, CONFIRMADA, RECUSADA, CANCELADA, EXPIRADA"
    datetime criado_em
    datetime respondido_em
  }
```
