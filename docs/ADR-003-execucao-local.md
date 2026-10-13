# ADR-003: Execução local, sem hospedagem, no MVP

**Status:** Aceito  |  **Data:** 2026-10-12  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

O MVP é um trabalho acadêmico para demonstrar o conceito. Ainda não há usuários reais.

Hospedar o sistema exigiria custo, configuração e cuidados extras de segurança em produção, o que foge do prazo e do objetivo da disciplina.

## Decisão

Rodar o sistema **localmente**, no computador da equipe, durante o MVP. O código fica no GitHub e o README traz o passo a passo para qualquer pessoa executar.

## Consequências

(+) Custo zero.

(+) Menos configuração, sobrando mais tempo para as funcionalidades.

(+) Os dados de teste ficam sob controle da equipe.

(-) Só quem roda o projeto na própria máquina consegue acessar.

(-) Não dá para testar com outros alunos pelo celular.

(-) Se o projeto continuar, será preciso escolher uma hospedagem e registrar em um novo ADR.

## Alternativas rejeitadas

- Hospedagem em nuvem (Vercel, Render, AWS etc.): custo e configuração desnecessários para o escopo atual.

- Servidor próprio da universidade: depende de autorização e infraestrutura fora do controle da equipe.

## Links

- Substitui: nenhum

- Relacionado: ADR-001, ADR-002, ADR-004

- Evidências: README.md do repositório
