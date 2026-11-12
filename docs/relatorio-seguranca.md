# Relatório de segurança do MVP Caroville

Data da análise: 11/11/2026 · Versão analisada: commit `9b8e3b2` (branch `main`) · Autores: Pedro e Lucas Felipe

## 1. Objetivo e método

Atividade da disciplina: (1) listar as vulnerabilidades do MVP e (2) corrigir e documentar como foi feito.

Usamos a skill de auditoria da Cloudflare (`cloudflare/security-audit-skill`) e fizemos a validação por conta própria. O trabalho teve duas etapas:

1. **Auditoria com a skill (rodada 1).** Rodamos a skill de verdade, pelo Claude Code, no código **original** (antes das correções), com o perfil `quick` (3 agentes caçadores, 1 revisor de cobertura e 8 verificadores). Como o Windows não tem o sandbox que a skill exige, ela não executou o código: tudo foi análise do código-fonte, e por regra da skill nenhum achado pode ser marcado como "confirmado" sem rodar. Ela devolveu **6 pistas "needs_validation"**, mais notas de reforço e uma área pendente (esgotamento de recursos). Os arquivos originais estão em `docs/auditoria-skill/` (`REPORT.md`, `NEEDS-VALIDATION.md`, `run-metadata.json`).
2. **Validação própria.** Rodamos a API em um banco de teste e reproduzimos cada pista (e as nossas, da leitura do código) antes e depois das correções. Critérios: **confirmada** = código lido + problema reproduzido rodando; **rejeitada** = hipótese testada e a proteção funciona. Só entra como vulnerabilidade o que quebra uma fronteira de segurança de verdade; o resto é risco residual (seção 6). Gravidade = probabilidade × impacto.

Resultado da skill, resumido: 0 confirmadas (por falta de sandbox), 6 pistas, 2 hipóteses rejeitadas, 1 área pendente. Das 6 pistas, **5 foram confirmadas por nós rodando o código** (as pistas 1, 2, 4, 5 e 6) e a 3 (Vite) foi confirmada pela versão instalada e pelo `npm audit` (não explorada). A tabela da seção 3 liga cada pista da skill ao nosso ID.

**Escopo:** backend (FastAPI + PostgreSQL), frontend (React) e arquivos de configuração. **Fora do escopo:** servidor de produção, HTTPS, e-mail real (o MVP roda local).

**Como reproduzimos:** script que chama a API em memória (`TestClient`) contra o banco de teste, antes e depois das correções. A suíte automática passou de 83 para **106 testes**, todos passando (23 novos em `backend/tests/test_seguranca.py`).

## 2. Resumo

| ID | Vulnerabilidade | Gravidade | Situação |
|----|-----------------|-----------|----------|
| VULN-01 | Link de confirmação de e-mail devolvido na resposta do cadastro | Alta | Corrigida |
| VULN-02 | Chave de assinatura do token (SECRET_KEY) padrão e pública | Alta | Corrigida |
| VULN-03 | Senha do banco padrão no código (`postgres:postgres`) | Média | Corrigida |
| VULN-04 | Bloqueio de login por e-mail permite travar a conta de outra pessoa; memória sem limite | Média | Corrigida |
| VULN-05 | Tempo de resposta do login revela se o e-mail existe | Média | Corrigida |
| VULN-06 | Senha com mais de 72 bytes causa erro 500 | Baixa | Corrigida |
| VULN-07 | Documentação da API (`/docs`, `/openapi.json`) pública | Baixa | Corrigida |
| VULN-08 | Sem cabeçalhos de segurança HTTP | Baixa | Corrigida |
| VULN-09 | CORS aceitava qualquer método e cabeçalho | Baixa | Corrigida |
| VULN-10 | Dependências do backend sem versão fixa | Baixa | Corrigida |
| VULN-11 | Duas solicitações simultâneas na mesma carona causavam erro 500 | Baixa | Corrigida |
| VULN-12 | Dependências do frontend com falhas conhecidas (Vite 5.4.11, React Router 6.28) | Média | Corrigida (restam 2 avisos moderados, ver R9) |
| VULN-13 | Limite de 5 tentativas de login furado por requisições simultâneas | Baixa | Corrigida |

## 3. Detalhe e correções

### VULN-01 · Alta · Confirmação de e-mail sem acesso ao e-mail
- **Onde:** `backend/app/rotas_auth.py`, função `cadastrar`.
- **Problema:** a resposta do `POST /auth/cadastro` trazia o `link_confirmacao`. Qualquer pessoa podia cadastrar e confirmar **qualquer** e-mail `@univille.br` sem ter acesso à caixa de entrada, quebrando a RN01 (só comunidade Univille) e permitindo se passar por outra pessoa.
- **Evidência (antes):** cadastro → 201 com `link_confirmacao`; GET no link → 200; login → 200.
- **Correção:** nova variável `MODO_DEMO` (padrão `false`). O link só vai na resposta quando `MODO_DEMO=true`; o link continua aparecendo no terminal (e-mail simulado). O frontend (`Cadastro.jsx`) trata a resposta sem link e mostra "abra o link enviado ao seu e-mail".
- **Evidência (depois):** resposta sem o campo; login antes de confirmar → 403.
- **Teste:** `test_cadastro_nao_devolve_link_fora_do_modo_demo`.
- **Para apresentar em aula:** deixar `MODO_DEMO=true` no `.env`. Com e-mail real (futuro), usar `false`.

### VULN-02 · Alta · SECRET_KEY previsível
- **Onde:** `backend/app/config.py` e `.env.example`.
- **Problema:** se a variável não existisse, o código usava `"chave-apenas-para-desenvolvimento"`, que está no GitHub. O `.env.example` também trazia uma chave de exemplo. Quem conhece a chave **fabrica um token válido** para qualquer usuário e entra na conta dele.
- **Evidência (antes):** token assinado com a chave padrão → `GET /perfil` = 200.
- **Correção:** sem valor padrão. O servidor **não inicia** se `SECRET_KEY` faltar, tiver menos de 32 caracteres ou for uma chave de exemplo (mensagem explica como gerar). `.env.example` agora deixa o campo vazio. Além disso, `ler_token` passou a exigir `exp` e `sub` dentro do token.
- **Evidência (depois):** mesmo token forjado → 401.
- **Testes:** `test_servidor_recusa_chave_fraca`, `test_token_forjado_com_chave_antiga_e_recusado`, `test_token_sem_expiracao_e_recusado`, `test_token_alg_none_e_recusado`.

### VULN-03 · Média · Senha padrão do banco
- **Onde:** `config.py`. **Problema:** `DATABASE_URL` tinha padrão `postgres:postgres`, uma credencial conhecida que poderia ser usada sem ninguém perceber.
- **Correção:** sem padrão; o servidor não inicia sem `DATABASE_URL`. **Teste:** `test_servidor_recusa_sem_database_url`.

### VULN-04 · Média · Bloqueio de login usado para travar contas
- **Onde:** `rotas_auth.py`, dicionário `tentativas`.
- **Problema:** o bloqueio (RNF07) era por e-mail. Um estranho errava 5 vezes a senha de alguém e essa pessoa ficava 15 minutos sem entrar (negação de serviço dirigida). Além disso, o dicionário nunca era limpo e aceitava e-mails gigantes (consumo de memória).
- **Evidência (antes):** após 5 erros de outra pessoa, o dono com a senha certa recebeu 429.
- **Correção:** a chave do bloqueio agora é **(IP, e-mail)**; registros parados há mais de 15 minutos são apagados quando passam de 5000; e-mail com mais de 150 caracteres é recusado antes de ser guardado. A RN de 5 erros / 15 minutos continua igual.
- **Testes:** `test_bloqueio_nao_vale_para_outro_ip`, `test_memoria_de_tentativas_e_limpa`, `test_email_gigante_no_login_nao_e_guardado`.
- **Limite da correção:** quem está atrás do mesmo IP (ex.: rede da universidade com NAT) ainda compartilha o bloqueio. Ver risco residual R3.

### VULN-05 · Média · Enumeração de e-mails pelo tempo de resposta
- **Onde:** `rotas_auth.py`, função `entrar`.
- **Problema:** o bcrypt (lento) só rodava se o e-mail existisse. A diferença era mensurável e dizia quais e-mails têm conta.
- **Evidência (antes):** 0,087 s (existe) × 0,015 s (não existe). **Depois:** 0,090 s × 0,088 s.
- **Correção:** quando o e-mail não existe, compara com um hash falso (`HASH_FALSO`), gastando o mesmo tempo.
- **Teste:** `test_login_gasta_tempo_parecido_com_email_inexistente`.
- **Aceito:** o cadastro ainda responde 409 "E-mail já cadastrado". É o comportamento esperado de qualquer cadastro; evitar isso exigiria e-mail real.

### VULN-06 · Baixa · Erro 500 com senha longa
- **Onde:** `modelos.py` e `seguranca.py`. **Problema:** o bcrypt 5 recusa senhas acima de 72 bytes e a API respondia 500 (e mostrava o erro no servidor).
- **Correção:** o cadastro rejeita com 422 "A senha deve ter no máximo 72 caracteres"; o login responde 401. **Teste:** `test_senha_com_mais_de_72_bytes`.

### VULN-07 · Baixa · Documentação pública
- **Onde:** `main.py`. **Problema:** `/docs`, `/redoc` e `/openapi.json` mostravam todos os endpoints a qualquer um.
- **Correção:** só existem com `MODO_DEMO=true`; senão respondem 404. **Teste:** `test_docs_desligados_fora_do_modo_demo`.

### VULN-08 · Baixa · Sem cabeçalhos de segurança
- **Correção:** middleware em `main.py` com `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e `Cache-Control: no-store` (respostas com dados de usuário não ficam em cache). **Teste:** `test_cabecalhos_de_seguranca`.

### VULN-09 · Baixa · CORS aberto demais
- **Correção:** métodos limitados a GET, POST, PUT e DELETE e cabeçalhos a `Authorization` e `Content-Type`. A origem já era restrita ao frontend (porta 5173). **Teste:** `test_cors_so_metodos_usados`.

### VULN-10 · Baixa · Dependências sem versão fixa
- **Onde:** `backend/requirements.txt`. **Problema:** `pip install` pegava sempre a versão mais nova, então uma biblioteca comprometida ou com mudança incompatível entrava sem aviso.
- **Correção:** versões fixadas nas que já usamos e testamos (fastapi 0.162.0, uvicorn 0.54.0, psycopg 3.3.6, bcrypt 5.0.0, PyJWT 2.15.1, python-dotenv 1.2.4, pytest 9.2.0, httpx 0.28.1). O frontend já tinha versões fixas.
- **Observação:** o `npm audit` foi rodado (ver VULN-12). O `pip-audit` não rodou no nosso ambiente: antes da entrega, rodar `pip install pip-audit && pip-audit -r requirements.txt` na pasta `backend`.

### VULN-11 · Baixa · Erro 500 em solicitação simultânea
- **Onde:** `rotas_caronas.py`, `solicitar_carona`. **Problema:** o banco já impede duas solicitações ativas iguais (índice único), mas dois cliques ao mesmo tempo passavam pela checagem e o segundo recebia 500.
- **Correção:** o erro de duplicidade do banco é capturado e vira 409 "Você já tem uma solicitação ativa nesta carona". **Teste:** `test_solicitacao_duplicada_simultanea_da_409`. (Esta é confirmada pela leitura do código e coberta pelo teste; não é uma falha de acesso, só de tratamento de erro.)

### VULN-12 · Média · Dependências do frontend com falhas conhecidas
- **Onde:** `frontend/package.json` e `package-lock.json`. Achado pela skill (pista 3) e ampliado pelo nosso `npm audit`.
- **Problema:** o Vite 5.4.11 tem as falhas CVE-2025-24010 e CVE-2025-30208. Enquanto o `npm run dev` roda, um site aberto no navegador pode ler arquivos locais da máquina do desenvolvedor, inclusive o `backend/.env` (e daí a `SECRET_KEY`). O `npm audit` ainda apontou falhas no `@remix-run/router`/`react-router-dom` 6.28 (redirecionamento aberto, gravidade alta) e no `esbuild` usado pelo Vite.
- **Evidência (antes):** `npm audit` com 5 vulnerabilidades (1 moderada, 4 altas). A exploração do Vite **não** foi reproduzida (a skill também não, por falta de sandbox); a confirmação é pela versão instalada e pelos avisos oficiais.
- **Correção:** `vite` 5.4.11 → **6.4.6**, `@vitejs/plugin-react` 4.3.4 → **4.7.0**, `react-router-dom` 6.28.0 → **6.30.6** (versões fixas, `package-lock.json` atualizado). Conferido: `npm run build` funciona e o servidor de desenvolvimento sobe.
- **Evidência (depois):** `npm audit` com 2 avisos moderados, ambos do `react-router` (ver R9).

### VULN-13 · Baixa · Limite de tentativas de login furado por simultaneidade
- **Onde:** `rotas_auth.py`, função `entrar`. Achado pela skill (pista 5).
- **Problema:** o servidor lia o contador, depois conferia a senha (lento) e só então somava o erro. Várias requisições juntas passavam todas pela leitura antes de qualquer soma, e o atacante testava mais de 5 senhas por janela.
- **Evidência (antes):** teste com 10 requisições ao mesmo tempo: 6 senhas chegaram a ser conferidas (limite: 5).
- **Correção:** a tentativa é **reservada antes** de conferir a senha, dentro de uma trava (`threading.Lock`). Passou de 5, responde 429 sem nem conferir a senha. Se a senha estiver certa, o contador zera como antes.
- **Teste:** `test_tentativas_simultaneas_nao_passam_do_limite` (falha no código antigo e passa no novo).

### Ligação com as pistas da skill

| Pista da skill | Nosso ID | Situação |
|---|---|---|
| 1. Cadastro devolve o token de confirmação | VULN-01 | Confirmada e corrigida |
| 2. Chave JWT padrão pública | VULN-02 | Confirmada e corrigida |
| 3. Vite 5.4.11 lê arquivos locais | VULN-12 | Corrigida (não explorada) |
| 4. Bloqueio de login usado contra a vítima | VULN-04 | Confirmada e corrigida (por IP) |
| 5. Contador de tentativas não atômico | VULN-13 | Confirmada e corrigida |
| 6. Memória de tentativas sem limite | VULN-04 | Confirmada e corrigida |

Achados **só nossos** (a skill não apontou): VULN-03, 05, 07, 08, 09 e 11 (esta última a skill citou apenas como nota de reforço). A skill fez o contrário também: VULN-12 e VULN-13 vieram dela.

## 4. Resumo das mudanças por arquivo

| Arquivo | Mudança |
|---------|---------|
| `backend/app/config.py` | Sem valores padrão para banco e chave; valida a chave; `MODO_DEMO` |
| `backend/app/seguranca.py` | Exige `exp`/`sub`; limite de 72 bytes; hash falso |
| `backend/app/rotas_auth.py` | Link só no modo demo; bloqueio por (IP, e-mail) com limpeza e trava; tempo igual no login |
| `backend/app/modelos.py` | Senha máxima de 72 caracteres |
| `backend/app/main.py` | Docs só no modo demo; cabeçalhos; CORS restrito |
| `backend/app/rotas_caronas.py` | Duplicidade vira 409 |
| `backend/requirements.txt`, `.env.example` | Versões fixas; chave vazia + `MODO_DEMO` |
| `frontend/src/paginas/Cadastro.jsx` | Aceita resposta sem link |
| `frontend/package.json`, `package-lock.json` | Vite 6.4.6, plugin-react 4.7.0, react-router-dom 6.30.6 |
| `docs/auditoria-skill/` | Saída original da skill da Cloudflare |
| `backend/tests/` | `conftest.py` ajustado; novo `test_seguranca.py` |
| `README.md`, `docs/api-endpoints.md` | Variáveis novas e regra do link |

## 5. Hipóteses testadas e descartadas (não são vulneráveis)

| Hipótese | Por que foi descartada |
|----------|------------------------|
| Injeção de SQL | Todas as consultas usam parâmetros (`%s`). Teste: `test_sql_injection_no_login_e_na_busca` |
| Acessar/alterar veículo, solicitação ou carona de outro usuário (IDOR) | Toda rota confere o dono (`usuario_id`/`motorista_id`) e responde 403/404. Teste: `test_nao_acessa_veiculo_de_outro_usuario` |
| Token JWT com algoritmo `none` ou trocado | O algoritmo é fixado em HS256. Teste: `test_token_alg_none_e_recusado` |
| XSS no frontend | O React escapa o texto; não há `dangerouslySetInnerHTML` nem `eval` |
| Ver telefone e placa antes do aceite (RN10) | Só motorista e passageiro CONFIRMADO recebem. Teste: `test_telefone_e_placa_ocultos_antes_do_aceite` |
| Vaga vendida em duplicidade | Travas `FOR UPDATE` e restrições no banco |

## 6. Riscos residuais (aceitos no MVP)

| ID | Risco | Por que aceitamos / o que fazer em produção |
|----|-------|---------------------------------------------|
| R1 | Token guardado em `localStorage` e sem revogação (vale até expirar, 2 h) | Padrão em SPAs simples. Produção: cookie `HttpOnly` + CSP |
| R2 | Sem HTTPS | MVP roda local (decisão ADR-003). Produção: HTTPS obrigatório |
| R3 | Bloqueio de login compartilhado por quem usa o mesmo IP; sem limite geral de requisições | Produção: limite por rota em proxy/gateway |
| R4 | Usuários do `seed.sql` têm senha conhecida (`senha1234`) | Nunca carregar o seed em produção |
| R5 | O e-mail simulado imprime o link de confirmação no terminal | Some quando houver envio real de e-mail |
| R6 | Dados da carona (rua, ponto de encontro) visíveis para qualquer usuário logado | É a função do app (busca). Telefone e placa continuam protegidos (RN10) |
| R7 | Link de confirmação via GET e reutilizável por 24 h | Baixo impacto: só marca o e-mail como confirmado |
| R8 | Sem recuperação de senha nem log de auditoria | Fora do escopo do MVP |
| R9 | `npm audit` ainda mostra 2 avisos moderados no `react-router` 6 (redirecionamento aberto por barra invertida e uma falha de renderização no servidor, que o projeto não usa). A correção exige React Router 7 (mudança grande) | O app só navega para caminhos fixos e não usa renderização no servidor. Migrar para a v7 em produção |
| R10 | **Esgotamento de recursos (área que a skill deixou pendente):** listas sem paginação, sem limite de caronas/veículos por usuário, o cadastro roda bcrypt sem limite de requisições e `atualizar_status_automaticos` faz atualizações na tabela inteira a cada requisição | Corrigir exigiria mudar regras e telas. Produção: paginação, limites por usuário e limite de requisições no proxy |
| R11 | Notas de reforço da skill **não** corrigidas: o link de confirmação aparece no terminal e na URL; tokens sem `iss`/`aud`; duas confirmações simultâneas de motoristas podem sobrepor horários do mesmo passageiro (RN12); `cancelar_solicitacao` trava a carona antes de conferir o dono; telefone guardado como digitado; 403 e 404 distinguem se o id existe; ids de rota usados sem validar no frontend; Google Fonts de terceiro | Impacto baixo no MVP local; ficam como melhoria futura |

## 7. Como repetir a verificação

```
cd backend
venv\Scripts\python -m pytest -q          (esperado: 106 passed)
venv\Scripts\python -m pytest tests/test_seguranca.py -v
```
Observação: o servidor agora exige `SECRET_KEY` forte no `.env`. Para a demonstração use `MODO_DEMO=true`.
