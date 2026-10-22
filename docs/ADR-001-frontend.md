# ADR-001: Escolha do framework de frontend

**Status:** Aceito  |  **Data:** 2026-10-12  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

O Caroville precisa de telas que funcionem bem em celular e computador: login, busca de caronas, oferta de carona e solicitações.

A equipe é pequena, ainda está aprendendo e precisa entregar o MVP em pouco tempo. As telas já foram prototipadas no Figma e se repetem bastante (cards de carona, formulários).

## Decisão

Usar **React com Vite** para construir o frontend como uma aplicação web responsiva.

## Consequências

(+) Muito material de estudo e comunidade grande.

(+) O Vite inicia e atualiza o projeto rápido durante o desenvolvimento.

(+) Componentes reutilizáveis facilitam repetir telas parecidas.

(-) Exige aprender JavaScript e conceitos de React (componentes e estado).

(-) O React não define navegação nem organização do projeto, então será preciso escolher bibliotecas extras.

## Alternativas rejeitadas

- Vue: boa opção, mas a equipe tem menos material de apoio e referências disponíveis.

- Angular: mais completo, porém mais pesado e com aprendizado mais longo para um MVP.

- HTML, CSS e JavaScript puros: ficaria difícil de manter conforme o número de telas crescer.

## Links

- Substitui: nenhum

- Relacionado: [ADR-004](ADR-004-backend.md) (backend), [protótipos no Figma](https://www.figma.com/design/SCf876FNOK081GMjxVszv8)

- Evidências: https://www.figma.com/design/SCf876FNOK081GMjxVszv8
