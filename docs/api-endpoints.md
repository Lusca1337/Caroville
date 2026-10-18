# Documentação dos endpoints (API do Caroville)

A API é feita em Python com FastAPI. Com o backend rodando, a documentação interativa (onde dá para testar cada endpoint) fica em `http://localhost:8000/docs`.

- **Endereço base:** `http://localhost:8000`
- **Formato:** JSON
- **Login:** os endpoints marcados com "Sim" na coluna Login exigem o cabeçalho `Authorization: Bearer <token>`. O token vem do `POST /auth/login`.
- **Erros:** sempre no formato `{"detail": "mensagem"}`, com a mensagem em português para mostrar ao usuário.
- **Datas e horários:** formato `2026-10-20T18:00` (horário local, sem fuso).

Códigos de resposta usados: `200` e `201` (sucesso), `400` (link inválido), `401` (sem login ou sessão expirada), `403` (sem permissão), `404` (não encontrado), `409` (regra de negócio impede a ação), `422` (dados inválidos), `429` (login bloqueado).

## 1. Autenticação (US01)

| Método | Caminho | Login | O que faz | Regras e erros |
|--------|---------|:-----:|-----------|----------------|
| POST | `/auth/cadastro` | Não | Cria a conta (RF01) | RN01: só e-mail `@univille.br` (422 "Use seu e-mail institucional"). E-mail repetido: 409. Senha de no mínimo 8 caracteres e telefone com DDD: 422 |
| GET | `/auth/confirmar-email?token=...` | Não | Confirma o e-mail pelo link (RF02) | Link inválido ou expirado: 400 |
| POST | `/auth/login` | Não | Devolve o token (RF03) | E-mail ou senha errados: 401. E-mail não confirmado: 403 "Confirme seu e-mail". 5 senhas erradas seguidas: bloqueio de 15 minutos (429) |

O logout não tem endpoint: o frontend apaga o token guardado.

Como o MVP não envia e-mail de verdade, a resposta do cadastro traz o `link_confirmacao`, e o mesmo link aparece no terminal do backend.

## 2. Perfil e veículo (US06)

| Método | Caminho | Login | O que faz | Regras e erros |
|--------|---------|:-----:|-----------|----------------|
| GET | `/perfil` | Sim | Dados do usuário logado | 401 sem login |
| PUT | `/perfil` | Sim | Altera nome, curso e telefone (RF04) | Validações de nome, curso e telefone: 422 |
| GET | `/veiculos` | Sim | Lista os meus veículos | |
| POST | `/veiculos` | Sim | Cadastra veículo (RF05) | Veículo com 2 a 8 lugares: 422 |
| PUT | `/veiculos/{id}` | Sim | Altera um veículo meu | Veículo de outra pessoa ou inexistente: 404 |
| DELETE | `/veiculos/{id}` | Sim | Exclui um veículo meu | Veículo já usado em caronas: 409 |
| GET | `/locais` | Não | Lista os locais (bairros e campus) para saída e destino | |

## 3. Caronas (US02 e US03)

| Método | Caminho | Login | O que faz | Regras e erros |
|--------|---------|:-----:|-----------|----------------|
| POST | `/caronas` | Sim | Publica uma carona (RF06) | RN02: sem veículo, 409 "Cadastre um veículo no seu perfil...". RN03: de 1 a 4 vagas (422). RN04: saída com pelo menos 1 hora de antecedência (422 "Informe um horário futuro"). Saída diferente do destino (422) |
| GET | `/caronas?origem_id=&destino_id=&horario=` | Sim | Busca caronas abertas com saída até 30 minutos antes ou depois do horário (RF07) | Parâmetro faltando ou data inválida: 422. Lista vazia quando não acha nada (o frontend mostra "Nenhuma carona encontrada") |
| GET | `/caronas/{id}` | Sim | Detalhes da carona (RF08) | Inexistente: 404. RN10: `telefone_motorista` só vem depois que o meu pedido é aceito |
| POST | `/caronas/{id}/solicitacoes` | Sim | Pede uma vaga (RF09) | RN05: não pode na própria carona (409). RN06: um pedido ativo por carona (409). Lotada: 409 "Carona lotada". Cancelada ou concluída: 409 |

## 4. Solicitações (US04)

| Método | Caminho | Login | O que faz | Regras e erros |
|--------|---------|:-----:|-----------|----------------|
| GET | `/caronas/{id}/solicitacoes` | Sim | O motorista vê os pedidos da carona | Só o motorista (403). RN10: o telefone do passageiro só aparece se o pedido foi confirmado |
| POST | `/solicitacoes/{id}/aceitar` | Sim | O motorista aceita o pedido (RF10, RF11) | Só o motorista (403). RN07: sem vaga, 409 "Carona lotada"; ao aceitar, as vagas diminuem em 1 e, chegando a 0, a carona vira "Lotada". RN12: passageiro com outra carona confirmada a menos de 1 hora (409). Pedido já respondido (409) |
| POST | `/solicitacoes/{id}/recusar` | Sim | O motorista recusa o pedido (RF10) | Só o motorista (403). Pedido já respondido (409) |

## 5. Minhas caronas e cancelamentos (US05)

| Método | Caminho | Login | O que faz | Regras e erros |
|--------|---------|:-----:|-----------|----------------|
| GET | `/minhas/oferecidas` | Sim | Caronas que eu ofereci, com a quantidade de pedidos pendentes (RF14) | |
| GET | `/minhas/solicitadas` | Sim | Caronas que eu pedi, com o status de cada pedido (RF14) | |
| POST | `/solicitacoes/{id}/cancelar` | Sim | O passageiro cancela o pedido (RF12) | RN08: só até 2 horas antes da saída (409 "Prazo de cancelamento encerrado"). Se estava confirmado, a vaga volta |
| POST | `/caronas/{id}/cancelar` | Sim | O motorista cancela a carona (RF13) | Só o motorista (403). RN08: prazo de 2 horas (409). RN09: todos os pedidos pendentes e confirmados viram "Cancelada" |

Atualizações automáticas, feitas sempre que alguém consulta a API:
- **RN11:** pedidos pendentes de caronas que já saíram viram "Expirada".
- **RN13:** caronas que já saíram e não foram canceladas viram "Concluída".

Os avisos por e-mail (RF15) são simulados e aparecem no terminal do backend.

## Exemplos

**Cadastro:** `POST /auth/cadastro`
```json
{
  "nome": "Ana Souza",
  "email": "ana@univille.br",
  "curso": "Direito",
  "telefone": "(47) 91111-2222",
  "senha": "minhasenha1"
}
```
Resposta `201`:
```json
{
  "mensagem": "Conta criada! Confirme seu e-mail para entrar.",
  "link_confirmacao": "http://localhost:8000/auth/confirmar-email?token=..."
}
```

**Login:** `POST /auth/login`
```json
{ "email": "ana@univille.br", "senha": "minhasenha1" }
```
Resposta `200`:
```json
{ "token": "eyJhbGciOi..." }
```

**Publicar carona:** `POST /caronas` (com o token no cabeçalho)
```json
{
  "origem_id": 2,
  "destino_id": 1,
  "saida_em": "2026-10-20T18:00",
  "vagas_total": 3,
  "ponto_encontro": "Praça da Bandeira",
  "observacoes": "Saio pontualmente"
}
```
O `veiculo_id` é opcional: sem ele, a API usa o primeiro veículo do motorista. Resposta `201`:
```json
{ "mensagem": "Carona publicada com sucesso", "id": 7 }
```

**Buscar caronas:** `GET /caronas?origem_id=2&destino_id=1&horario=2026-10-20T18:15`

Resposta `200`:
```json
[
  {
    "id": 7,
    "saida_em": "2026-10-20T18:00:00",
    "origem": "Costa e Silva",
    "destino": "Campus Univille",
    "vagas_total": 3,
    "vagas_disponiveis": 3,
    "ponto_encontro": "Praça da Bandeira",
    "observacoes": "Saio pontualmente",
    "status": "ABERTA",
    "motorista_id": 1,
    "motorista_nome": "Lucas Felipe",
    "veiculo_modelo": "Fiat Argo",
    "veiculo_cor": "Prata",
    "origem_id": 2,
    "destino_id": 1
  }
]
```
O detalhe da carona (`GET /caronas/{id}`) devolve os mesmos campos mais `sou_motorista`, `minha_solicitacao_id`, `minha_solicitacao_status` e `telefone_motorista`.

**Erro:** `POST /auth/cadastro` com e-mail de outro domínio, resposta `422`:
```json
{ "detail": "Use seu e-mail institucional" }
```

## Status

- **Carona:** `ABERTA`, `LOTADA`, `CANCELADA`, `CONCLUIDA`
- **Solicitação:** `PENDENTE`, `CONFIRMADA`, `RECUSADA`, `CANCELADA`, `EXPIRADA`

## Usuários de teste (dados iniciais do `seed.sql`)

Todos com a senha `senha1234`: `lucas@univille.br` (tem veículo), `maria@univille.br` e `joao@univille.br`.
