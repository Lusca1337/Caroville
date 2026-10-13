# ADR-002: Escolha do banco de dados relacional

**Status:** Aceito  |  **Data:** 2026-10-12  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

Os dados do sistema têm relações claras entre usuários, veículos, caronas e solicitações, como mostra o DER.

Também existem regras que precisam ser garantidas pelo sistema, como e-mail único, vagas dentro do limite e uma solicitação ativa por passageiro em cada carona.

## Decisão

Usar o **PostgreSQL** como banco de dados do MVP, seguindo o modelo do DER (docs/05-modelagem-de-dados.md).

## Consequências

(+) Garante chaves, relacionamentos e restrições direto no banco.

(+) Gratuito e bem documentado.

(+) Boa performance para buscas com filtros (saída, destino e horário).

(-) Exige instalar e configurar o banco em cada computador da equipe.

(-) Mudar a estrutura das tabelas depois pede cuidado (migrações).

## Alternativas rejeitadas

- MySQL: também serviria, mas o PostgreSQL tem recursos de restrição mais completos.

- MongoDB: os dados são muito relacionados, então um banco de documentos não combina com o DER.

- SQLite: simples, porém limitado se o projeto crescer para vários usuários ao mesmo tempo.

## Links

- Substitui: nenhum

- Relacionado: ADR-004 (backend), DER (docs/05-modelagem-de-dados.md)

- Evidências: https://www.postgresql.org/docs/
