# Testes

Os testes automáticos ficam em `backend/tests` e usam **pytest**. Eles chamam a API de verdade e conferem o resultado no banco PostgreSQL. Como rodar: veja a seção "Como executar os testes" do [README](../README.md).

Cada teste cria os próprios usuários e caronas (e-mails `teste.xxxx@univille.br`) e tudo é apagado no final, então os dados do seed não são alterados.

## O que cada arquivo cobre

| Arquivo | Histórias, regras e requisitos testados |
|---------|------------------------------------------|
| `test_us01_cadastro_login.py` | US01: cadastro, confirmação de e-mail, login; RN01 (e-mail `@univille.br`); RNF06 (senha com hash); RNF07 (5 erros bloqueiam o login); rotas protegidas |
| `test_us06_perfil_veiculo.py` | US06: ver e editar perfil, cadastrar, editar e excluir veículo; placa nos padrões antigo e Mercosul, placa inválida e placa repetida; veículo de outra pessoa; veículo já usado em carona |
| `test_us02_oferecer_carona.py` | US02: oferecer carona; RN02 (precisa de veículo); RN03 (1 a 4 vagas); RN04 (1 hora de antecedência); RN14 (Campus como saída ou destino) |
| `test_us03_buscar_solicitar.py` | US03: busca (janela de 30 minutos, filtros), detalhe, solicitar vaga; RN05 (não pedir a própria carona); RN06 (sem pedido duplicado); RN10 (telefone só depois do aceite) |
| `test_us04_gerenciar_solicitacoes.py` | US04: ver, aceitar e recusar; RN07 (vaga descontada, carona lotada); RN12 (horários com menos de 1 hora de diferença); gravação no banco |
| `test_us05_minhas_e_cancelamentos.py` | US05: minhas caronas; cancelar solicitação e carona; RN08 (prazo de 2 horas); RN09 (cancelar carona cancela os pedidos) |
| `test_regras_de_tempo.py` | RN11 (pedido pendente expira) e RN13 (carona que já saiu vira concluída) |
| `test_integracao_front_back.py` | CORS do frontend, formato dos erros que as telas mostram e o fluxo completo cadastro → carona confirmada |

Critérios de aceite, validações de entrada e tratamento de erros estão distribuídos nesses arquivos: cada teste confere o código HTTP (200/201, 401, 403, 404, 409, 422, 429) e a mensagem em português devolvida.

## Roteiro manual das telas (frontend + backend + banco)

Com banco, backend e frontend rodando e o seed carregado (`lucas@univille.br`, `maria@univille.br`, `joao@univille.br`, senha `senha1234`):

| # | Passo | Resultado esperado |
|---|-------|--------------------|
| 1 | Abrir http://localhost:5173 sem estar logado | Vai para a tela de Login |
| 2 | Entrar com `maria@univille.br` e senha errada | Mensagem "E-mail ou senha incorretos" |
| 3 | Entrar com `maria@univille.br` e `senha1234` | Abre "Buscar caronas" |
| 4 | Cadastrar uma conta com e-mail que não é `@univille.br` | Mensagem "Use seu e-mail institucional" |
| 5 | Buscar Costa e Silva → Campus Univille no horário de uma carona do seed | A carona do Lucas aparece |
| 6 | Abrir a carona e clicar em "Solicitar carona" | Status "Pendente"; o telefone do motorista não aparece |
| 7 | Sair e entrar como `lucas@univille.br`; abrir "Minhas" → a carona → "Ver solicitações" | O pedido da Maria aparece |
| 8 | Aceitar o pedido | Vagas diminuem em 1; telefone da Maria aparece |
| 9 | Entrar de novo como Maria e abrir a carona | Status "Confirmada" e telefone do motorista visível |
| 10 | Como Lucas, abrir a própria carona | Não há botão de solicitar vaga |
| 11 | Em "Oferecer", escolher bairro → bairro | O destino só oferece o Campus Univille |
| 12 | No cadastro, digitar o telefone com letras | Só números são aceitos e a máscara `(47) 9 9999-9999` é aplicada |
| 13 | Em "Oferecer", tentar uma data passada | O campo não aceita |
| 14 | Perfil: editar nome e telefone, recarregar a página | Os dados continuam alterados (vieram do banco) |
