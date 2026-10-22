# ADR-005: Autenticação com e-mail institucional e JWT

**Status:** Aceito  |  **Data:** 2026-10-12  |  **Autores:** Lucas Felipe, Pedro Placidina

## Contexto

O Caroville é voltado só para estudantes da Univille. Como envolve encontrar pessoas e dividir o carro, é importante saber que o usuário é realmente do meio universitário.

O sistema também precisa proteger as senhas (RNF06), limitar tentativas de login (RNF07) e esconder o telefone e a placa do veículo até a carona ser aceita (RNF08).

## Decisão

- Cadastro e login somente com **e-mail institucional** (RN01), com verificação por e-mail.

- Senhas guardadas com **hash bcrypt**, nunca em texto puro.

- Após o login, o usuário recebe um **token JWT** com validade curta, enviado em cada requisição à API.

- Bloqueio do login por 15 minutos após 5 senhas erradas seguidas.

- No MVP o e-mail de verificação é **simulado**: o link de confirmação aparece no terminal do backend e na resposta do cadastro, e a tela de cadastro tem um botão para confirmar. O envio real fica para quando o sistema for hospedado ([ADR-003](ADR-003-execucao-local.md)).

## Consequências

(+) Só quem tem e-mail da universidade entra, o que aumenta a confiança entre os usuários.

(+) Sem guardar senha em texto puro, o risco em caso de vazamento é menor.

(+) JWT dispensa guardar sessões no servidor e é simples de usar com a API.

(-) Quem não tem e-mail institucional (ex.: ex-aluno) fica de fora.

(-) Token roubado vale até expirar, por isso a validade precisa ser curta.

(-) Para usuários reais, é preciso configurar um serviço de envio de e-mail. No MVP isso foi adiado e o envio é simulado.

## Alternativas rejeitadas

- Login com Google ou redes sociais: não garante que a pessoa seja da universidade.

- Sessões guardadas no servidor: exigem mais estrutura e armazenamento para um MVP.

- Cadastro livre sem verificação: facilita contas falsas e reduz a segurança.

## Links

- Substitui: nenhum

- Relacionado: [ADR-004](ADR-004-backend.md), [RN01](01-requisitos-funcionais.md), [RNF06, RNF07 e RNF08](02-requisitos-nao-funcionais.md)

- Evidências: https://jwt.io/introduction
