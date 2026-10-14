# Caroville

Plataforma de caronas para estudantes da Univille. Conecta alunos que **oferecem carona** com alunos que **precisam de transporte**, a partir de local de saída, destino, horário e número de vagas.

**Autores:** Lucas Felipe, Pedro Placidina
**Instituição:** Universidade da Região de Joinville - Univille

## Documentação técnica (MVP)

| # | Documento | Conteúdo |
|---|-----------|----------|
| 1 | [Requisitos funcionais, histórias de usuário e regras de negócio](docs/01-requisitos-funcionais.md) | RF, histórias com critérios de aceite BDD, RN |
| 2 | [Requisitos não funcionais](docs/02-requisitos-nao-funcionais.md) | RNF mensuráveis |
| 3 | [Protótipos de tela](docs/03-prototipos.md) | Telas no Figma ligadas às histórias |
| 4 | [Registros de decisão de arquitetura (ADRs)](docs/adrs/) | Decisões tecnológicas (veja a tabela abaixo) |
| 5 | [Modelagem de dados (DER)](docs/05-modelagem-de-dados.md) | DER e restrições |

**Protótipo no Figma:** [Caroville - Protótipos MVP](https://www.figma.com/design/SCf876FNOK081GMjxVszv8)

## Decisões de arquitetura (ADRs)

| ADR | Decisão | Status |
|-----|---------|--------|
| [ADR-001](docs/ADR-001-frontend.md) | Frontend com React | Aceito |
| [ADR-002](docs/ADR-002-banco-de-dados.md) | Banco de dados PostgreSQL | Aceito |
| [ADR-003](docs/ADR-003-execucao-local.md) | Execução local, sem hospedagem, no MVP | Aceito |
| [ADR-004](docs/ADR-004-backend.md) | Backend com Node.js e Express | Aceito |
| [ADR-005](docs/ADR-005-autenticacao.md) | Autenticação com e-mail institucional e JWT | Aceito |

## Visão geral da arquitetura

```mermaid
flowchart LR
  U["Estudante (celular ou computador)"] --> F["Aplicação web (frontend)"]
  F -->|"HTTPS"| B["API (backend)"]
  B --> D[("Banco de dados")]
  B --> E["Serviço de e-mail"]
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
