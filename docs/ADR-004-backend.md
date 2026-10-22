# ADR-004: Escolha da linguagem e do framework de backend

**Status:** Aceito  |  **Data:** 2026-10-14  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

O sistema precisa de uma API que valide as regras de negócio (vagas, solicitações, cancelamento), converse com o banco de dados e envie e-mails. No MVP o envio de e-mail é simulado: a mensagem aparece no terminal do backend (ver [ADR-005](ADR-005-autenticacao.md)).

A equipe é pequena, ainda está aprendendo e precisa entregar o MVP em pouco tempo, então a linguagem precisa ser simples de ler e exigir pouca configuração.

## Decisão

Usar **Python com FastAPI** para construir a API REST do Caroville.

## Consequências

(+) Sintaxe simples, que facilita aprender e revisar o código um do outro.

(+) O FastAPI valida os dados de entrada e gera a documentação da API automaticamente.

(+) Boa integração com PostgreSQL e com bibliotecas de bcrypt e JWT (ADR-002 e ADR-005).

(-) O frontend usa JavaScript e o backend usa Python, então a equipe trabalha com duas linguagens.

(-) O FastAPI é minimalista, então a equipe precisa definir a organização das pastas.

(-) É preciso aprender o básico do ambiente Python (ambiente virtual e instalação de pacotes).

## Alternativas rejeitadas

- Node.js com Express: manteria uma linguagem só, mas a equipe preferiu Python pela sintaxe mais simples.

- Java com Spring Boot: robusto, mas mais pesado e demorado de configurar para um MVP.

- Python com Django: também serviria, porém traz mais convenções para aprender do que o necessário.

- C# com ASP.NET: exige ambiente e ferramentas que a equipe ainda não domina.

## Links

- Substitui: versão anterior deste ADR (Node.js com Express)

- Relacionado: [ADR-001](ADR-001-frontend.md), [ADR-002](ADR-002-banco-de-dados.md), [ADR-005](ADR-005-autenticacao.md), [endpoints da API](api-endpoints.md)

- Evidências: https://fastapi.tiangolo.com/
