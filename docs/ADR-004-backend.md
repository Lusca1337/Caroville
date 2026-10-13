# ADR-004: Escolha da linguagem e do framework de backend

**Status:** Aceito  |  **Data:** 2026-10-12  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

O sistema precisa de uma API que valide as regras de negócio (vagas, solicitações, cancelamento), converse com o banco de dados e envie e-mails.

O frontend será feito em JavaScript (ADR-001), e a equipe quer reduzir a quantidade de linguagens para aprender.

## Decisão

Usar **Node.js com Express** para construir a API REST do Caroville.

## Consequências

(+) Mesma linguagem (JavaScript) no frontend e no backend.

(+) Express é simples, leve e tem muita documentação.

(+) Boa integração com PostgreSQL e com bibliotecas de autenticação.

(-) O Express é minimalista, então a equipe precisa definir a organização das pastas.

(-) JavaScript não tem checagem de tipos por padrão, o que pode causar erros que só aparecem na execução.

## Alternativas rejeitadas

- Java com Spring Boot: robusto, mas mais pesado e demorado de configurar para um MVP.

- Python com Django ou Flask: boas opções, mas adicionariam uma segunda linguagem ao projeto.

- C# com ASP.NET: exige ambiente e ferramentas que a equipe ainda não domina.

## Links

- Substitui: nenhum

- Relacionado: ADR-001, ADR-002, ADR-005

- Evidências: https://expressjs.com/
