# Caroville: Needs-Validation Leads (run 1)

These are source-grounded leads whose decisive evidence is blocked. **They have no severity and are not confirmed vulnerabilities.** Each was traced by a hunter and independently re-checked by a separate verifier against current source. They are listed in suggested triage order. Do not test them against any shared or deployed instance. Use the bounded local plans inside a sandbox, or answer the owner-side questions.

## 1. Registration returns the email-confirmation token, so email ownership (RF02) and institutional membership (RN01) are never proven

**Fingerprint:** `caroville:rotas_auth:cadastro-returns-email-confirmation-token`

POST /auth/cadastro creates the user, mints a confirmar_email JWT (sub = new user id, valid for 24 h) and always returns the confirmation link containing it in the 201 response body as link_confirmacao. No configuration flag gates this. An anonymous client can register any @univille.br address that is not yet registered, GET /auth/confirmar-email with the returned token, and then log in. The result is a verified, login-capable account obtained without controlling that mailbox, so the email_verificado gate does not prove Univille membership, which RN10 phone sharing assumes. It also allows squatting a real student's address: the owner later gets 409 'E-mail já cadastrado', and the code has no recovery or ownership-reclaim path. This is a documented MVP shortcut (docs/api-endpoints.md), and ADR-003 says the system runs only locally, so the impact depends on whether any instance is reachable by people other than the developer.

**Claimed root cause:** The proof-of-possession secret for the email address (the confirmar_email JWT) is delivered to the party being verified in the cadastro HTTP response (rotas_auth.py:32-37), not only to the mailbox. The email_verificado check at rotas_auth.py:75 therefore cannot tell mailbox owners from non-owners.

**Trace**

- *entrypoint*: `backend/app/rotas_auth.py:21` (cadastrar): Anonymous POST /auth/cadastro with any email that passes Cadastro.v_email (a single @, ending in @univille.br); no authentication is required.
- *propagation*: `backend/app/rotas_auth.py:32` (cadastrar): criar_token creates a confirmar_email JWT with sub = the new user id, valid for 24 h.
- *propagation*: `backend/app/rotas_auth.py:37` (cadastrar): The link containing the token is returned to the registrant in the 201 body as link_confirmacao.
- *propagation*: `backend/app/rotas_auth.py:49` (confirmar_email): The registrant presents the token to GET /auth/confirmar-email; after the type check at line 47, email_verificado is set to TRUE for sub.
- *sink*: `backend/app/rotas_auth.py:79` (entrar): Login passes the email_verificado gate at line 75 and an access token is issued for an email identity the caller never proved.

**Evidence**

- `backend/app/rotas_auth.py:37`: "link_confirmacao": link is returned in the 201 response body unconditionally (no dev-only flag).
- `backend/app/rotas_auth.py:75`: email_verificado is the only email-ownership gate before an access token is issued.
- `backend/app/modelos.py:43`: RN01 is only a syntactic domain-suffix check; it proves nothing about mailbox control.
- `docs/01-requisitos-funcionais.md:8`: RF02 requires the email to be confirmed through a link sent to the registered address.
- `docs/api-endpoints.md:23`: Documents that, because the MVP sends no real email, the cadastro response returns link_confirmacao.
- `frontend/src/paginas/Cadastro.jsx:26`: The SPA stores the returned link and confirms it with one click via confirmarEmail(link) (line 38).
- `docs/ADR-003-execucao-local.md:13`: The system is intended to run only locally during the MVP, so real-world exposure depends on deployment.

**Blockers**

- No OS-enforced sandbox was available on this host, so no target code was executed and there is no independently reproduced local observed result.
- Whether any instance running this code path is reachable by people other than the developer (ADR-003 says local only) is a deployment fact outside the source, and it decides whether the bypass has real-world impact.

**Resolution plan**

- **Local (sandboxed, dummy data):** In an isolated, network-less sandbox with a throwaway local Postgres loaded from backend/database/schema.sql, use the FastAPI TestClient fixture pattern from backend/tests/conftest.py. POST /auth/cadastro with {nome:'Teste', email:'naoepossuido@univille.br', curso:'Teste', telefone:'(47) 99999-0000', senha:'senhaforte1'}. Take link_confirmacao from the JSON response and GET its path and query (/auth/confirmar-email?token=...). Then POST /auth/login with the same email and password. Expect 200 with a token, which shows the account was verified without mailbox access. Discard the database afterwards. Regression test: the cadastro response contains no token or link, and confirmation requires a value delivered only out of band (email or server log).
- **Owner-observed (no audit traffic):** Without sending any audit traffic, the owner confirms whether any instance running this code (a shared lab machine, demo server or tunnel) is reachable by anyone other than the developer. If so, deliver the token only by email, or log it behind a dev-only setting that is off by default, and remove link_confirmacao from the cadastro response.

## 2. The JWT signing key silently falls back to a public hard-coded value (or the documented placeholder)

**Fingerprint:** `backend/app/config.py:SECRET_KEY:public-fallback-signing-key`

SECRET_KEY is read from the environment and falls back to the hard-coded value 'chave-apenas-para-desenvolvimento' (backend/app/config.py:8). Nothing checks at startup whether the key is missing, known or short. The README tells users to copy backend/.env.example, whose SECRET_KEY placeholder 'troque-esta-chave-por-um-texto-grande-e-aleatorio' is also public. criar_token signs every access and email-confirmation token with this one key, and ler_token verifies with it (HS256 only). usuario_logado accepts any token with tipo='acesso' and loads the user named in its sub claim, with no other binding such as issuer, audience, session or revocation. If a running API uses either public value, anyone who can send it HTTP requests can mint {sub:<any user id>, tipo:'acesso', exp:<future>} and be authenticated as that user on every protected route: reading and editing the profile (including telefone), managing vehicles, requesting, accepting, refusing or cancelling seats, and cancelling rides. They can also mint tipo='confirmar_email' tokens to mark any account as verified. Whether this applies depends on the deployed key value and on reachability: uvicorn binds to loopback by default (README.md:118), and CORS only restricts browser cross-origin reads, not direct HTTP clients.

**Claimed root cause:** backend/app/config.py:8 uses os.getenv('SECRET_KEY', 'chave-apenas-para-desenvolvimento') and never rejects a missing key, a known literal (the fallback or the .env.example placeholder) or a short key. backend/app/seguranca.py:26 signs with it, :30 verifies with it, and usuario_logado (seguranca.py:33-53) trusts the verified token's sub as the authenticated principal.

**Trace**

- *entrypoint*: `backend/app/seguranca.py:33` (usuario_logado): FastAPI dependency used by every authenticated route; it takes the Bearer credential from the Authorization header via HTTPBearer(auto_error=False).
- *propagation*: `backend/app/config.py:8` (module): SECRET_KEY = os.getenv('SECRET_KEY', 'chave-apenas-para-desenvolvimento'), which is a public literal when the variable is unset; the value is never validated.
- *propagation*: `backend/app/seguranca.py:30` (ler_token): jwt.decode(token, SECRET_KEY, algorithms=['HS256']) accepts any token signed with the key in use.
- *propagation*: `backend/app/seguranca.py:45` (usuario_logado): The only claim checked after the signature is tipo == 'acesso', which an attacker can set.
- *sink*: `backend/app/seguranca.py:47` (usuario_logado): Loads the usuario row by the token's sub claim and returns it as the authenticated principal.

**Evidence**

- `backend/app/config.py:8`: Hard-coded fallback signing key with no startup validation.
- `backend/.env.example:2`: Public placeholder SECRET_KEY that the README tells users to copy into backend/.env.
- `README.md:83`: Documents the placeholder as the example SECRET_KEY value.
- `backend/app/seguranca.py:26`: criar_token signs with the same SECRET_KEY; rotas_auth.py:32 issues confirmation tokens and rotas_auth.py:79 issues access tokens with it.
- `backend/app/rotas_auth.py:47`: The confirm-email route checks only tipo == 'confirmar_email' on a token verified with the same key, so a forged token can verify any account.
- `README.md:118`: The documented run command 'python -m uvicorn app.main:app --reload' binds to 127.0.0.1 by default, which limits default reachability to the local host.

**Blockers**

- No OS-enforced sandbox was available on this host, so the API could not be run locally to show a forged token being accepted.
- Whether any running instance has SECRET_KEY unset or equal to the .env.example placeholder is a deployment fact; backend/.env values were deliberately not read.
- Reachability is a deployment fact. The documented uvicorn command binds to 127.0.0.1, so exposure beyond the local host depends on how the API is actually started or hosted. CORS does not stop direct HTTP clients.

**Resolution plan**

- **Local (sandboxed, dummy data):** In an isolated sandbox with no network, start a throwaway Postgres loaded with backend/database/schema.sql and seed.sql, then start the API with SECRET_KEY unset. Mint a token with jwt.encode({'sub':'2','tipo':'acesso','exp':now+600}, 'chave-apenas-para-desenvolvimento', algorithm='HS256') and call GET /perfil with 'Authorization: Bearer <token>'. Expect 200 with maria@univille.br's profile, which proves the forged identity was accepted. Repeat with SECRET_KEY set to 'troque-esta-chave-por-um-texto-grande-e-aleatorio'. As a control, a token signed with a different random key must get 401. Regression test for the fix: the app must refuse to start when SECRET_KEY is missing, equals either literal, or is shorter than 32 bytes.
- **Owner-observed (no audit traffic):** Without revealing the value, the owner confirms three things: that backend/.env (or the process environment) defines SECRET_KEY; that it is neither 'chave-apenas-para-desenvolvimento' nor 'troque-esta-chave-por-um-texto-grande-e-aleatorio' and is at least 32 random bytes; and whether uvicorn is ever started with --host 0.0.0.0 or otherwise exposed beyond 127.0.0.1.

## 3. The pinned Vite 5.4.11 dev server lets any website read local files, including backend/.env

**Fingerprint:** `frontend/package.json:vite@5.4.11:dev-server-cross-origin-file-read`

The frontend pins vite 5.4.11 (package.json and lockfile; the installed node_modules/vite/package.json also reports 5.4.11). That version predates the fixes for GHSA-vg6x-rcgg-rjx6 / CVE-2025-24010 (wildcard CORS by default on the dev server, fixed in 5.4.12) and CVE-2025-30208 (a server.fs allow/deny bypass via '?import&raw??', fixed in 5.4.15). In the installed source, an unset server.cors makes the server call corsMiddleware(undefined), which uses the cors package's default origin '*'. transformMiddleware calls ensureServingAccess only when rawRE or urlRE matches the request URL, and neither matches '/@fs/<abs>?import&raw??'. removeImportQuery then rewrites the query to '?raw?', doTransform's removeTimestampQuery rewrites it to '?raw', and the asset plugin's load() reads the file with fsp.readFile and returns it as a JS string. The default fs.deny ['.env', '.env.*', '*.{crt,pem}'] and the fs.allow workspace root are never checked. So while a developer runs `npm run dev`, a page on any origin they visit could fetch http://localhost:5173/... and read the responses. It could learn the absolute project path (for example from the jsxDev fileName in /src/App.jsx, or by guessing) and then read backend/.env or any other file the developer's account can read. If .env holds SECRET_KEY, the attacker can forge HS256 access tokens for any account on that developer's backend. The impact is limited to developer machines while the dev server runs; ADR-003 says deployment is local-only.

**Claimed root cause:** frontend/package.json:18 pins a known-vulnerable vite 5.4.11 (lockfile line 1665). In the installed build: (a) _createServer runs corsMiddleware(typeof cors === 'boolean' ? {} : cors) whenever server.cors !== false, and with cors unset it passes undefined, which falls back to the cors package's default origin '*' (dep-CB_7IfJ-.js:41656); (b) transformMiddleware enforces ensureServingAccess only when rawRE /(\?|&)raw(?:&|$)/ or urlRE matches the raw request URL, but later normalization (removeImportQuery plus trailingSeparatorRE, then removeTimestampQuery in doTransform) turns '?import&raw??' into '?raw', and the asset plugin then reads the file unconditionally. frontend/vite.config.js:7 sets only port and strictPort, with no server.cors restriction and no fs hardening.

**Trace**

- *entrypoint*: `frontend/package.json:7` (scripts.dev): `npm run dev` runs `vite` and starts the dev server on localhost:5173; a cross-origin web page the developer visits can then send requests to it from the browser.
- *propagation*: `frontend/vite.config.js:7` (server): Only port 5173 and strictPort are set; there is no cors:false or origin allowlist and no fs.allow/deny override.
- *propagation*: `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:63087` (_createServer middlewares): With cors undefined, cors !== false holds and corsMiddleware(undefined) is installed (line 63088). The cors defaults at line 41656 give origin '*', so any origin can read responses.
- *propagation*: `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:61864` (transformMiddleware): ensureServingAccess runs only if rawRE or urlRE matches the request URL. '?import&raw??' matches neither, so the fs.allow/deny check is skipped; isImportRequest matches, removeImportQuery yields '?raw?', and the request goes to transformRequest.
- *propagation*: `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:51799` (doTransform): removeTimestampQuery strips the remaining trailing '?' via trailingSeparatorRE (line 16858), leaving a '?raw' module id.
- *sink*: `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:20316` (asset plugin load): rawRE now matches the id, so the plugin reads cleanUrl(id) with fsp.readFile and returns its contents as `export default "..."`, with no serving-access check.

**Evidence**

- `frontend/package.json:18`: "vite": "5.4.11"
- `frontend/package-lock.json:1665`: The lockfile resolves node_modules/vite to version 5.4.11.
- `frontend/node_modules/vite/package.json:3`: The installed vite reports version 5.4.11.
- `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:16868`: rawRE = /(\?|&)raw(?:&|$)/ does not match 'raw??'.
- `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:16849`: importQueryRE strips '?import&' to '?', turning '?import&raw??' into '?raw??', and trailingSeparatorRE (16858) then removes one trailing separator per call.
- `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:41656`: The bundled cors middleware defaults to origin: '*'.
- `frontend/node_modules/vite/dist/node/chunks/dep-CB_7IfJ-.js:63222`: The default fs.deny is ['.env', '.env.*', '*.{crt,pem}'], and its only enforcement point on this path (ensureServingAccess at 61864) is skipped.

**Blockers**

- No OS-enforced sandbox was available on this host, so the Vite dev server could not be started to observe the cross-origin file read; source shows every step but there is no end-to-end observed result.
- Whether a real internet page can reach localhost:5173 depends on the browser: Chrome's Private Network Access / Local Network Access controls may preflight or prompt public-to-loopback requests, which cannot be determined from source. A loopback-origin attacker page is enough for the local plan, but the 'any website' reach needs a browser-version observation.
- Whether backend/.env exists on a given developer machine and contains a real SECRET_KEY was deliberately not read, so the token-forgery consequence is inferred, not observed.

**Resolution plan**

- **Local (sandboxed, dummy data):** In a sandbox with networking limited to loopback and an empty environment: create a dummy canary file outside frontend/ (for example <scratch>/secret.txt containing 'canary'; do not use the real backend/.env). From frontend/, run the installed vite 5.4.11 with `node node_modules/vite/bin/vite.js --port 5173 --strictPort`. Serve a test page from a different loopback origin (for example http://127.0.0.1:9000) and run: (1) fetch('http://localhost:5173/src/App.jsx').then(r=>r.text()), expecting a successful read with Access-Control-Allow-Origin: * and a body that contains the absolute file path; (2) fetch('http://localhost:5173/@fs/<abs-path-with-forward-slashes>/secret.txt?import&raw??').then(r=>r.text()), expecting `export default "canary"`; (3) as a control, the same URL with '?raw' instead of '?import&raw??', expecting 403 Restricted; (4) step (2) repeated with a dummy file named '.env' in the scratch dir, to confirm the deny list is bypassed. Regression: after upgrading to the latest vite 5.4.x (>= 5.4.19) or setting server.cors to an explicit localhost origin, the cross-origin reads in (1) and (2) must fail and (2) must return 403.

## 4. An anonymous client can keep any user locked out of login with 5 wrong-password requests every 15 minutes

**Fingerprint:** `caroville:rotas_auth:login-lockout-keyed-by-email-victim-lockout`

The RNF07 lockout state is held in the in-memory tentativas dict and keyed only by the submitted email, after Login.v_email strips and lowercases it. An unauthenticated client who knows or guesses a victim's address sends 5 POST /auth/login requests with a wrong password, and the fifth sets bloqueado_ate to now + 15 minutes. Guessing is realistic because institutional addresses are predictable and POST /auth/cadastro returns 409 for addresses that already exist. Until the lock expires, every login for that email returns 429 before the database lookup and bcrypt check, so the owner's correct password is refused too. The counter is reset only by a successful login (line 78), which cannot be reached while the lock is active. Sending 5 more requests after each window ends keeps the victim locked out indefinitely. The repository has no password reset, alternate login path or per-requester dimension that would let the owner bypass the lock, and case or whitespace variants of the email map to the same key, so they do not help the owner either.

**Claimed root cause:** In entrar, the lockout check (backend/app/rotas_auth.py:58-62) runs before credential verification and its state is selected only by the target identity (tentativas.setdefault(dados.email, ...) at line 55). There is no binding to the requester and no path for the legitimate owner, so any third party can drive the failure counter for an account and deny its owner access to login.

**Trace**

- *entrypoint*: `backend/app/rotas_auth.py:54` (entrar): Unauthenticated POST /auth/login (route declared at line 53) with the victim's email and a wrong password.
- *propagation*: `backend/app/rotas_auth.py:55` (entrar): The counter entry is selected only by the normalized dados.email; no requester or IP component is part of the key.
- *propagation*: `backend/app/rotas_auth.py:72` (entrar): Once the attacker's failures reach MAX_TENTATIVAS (5), bloqueado_ate is set to now + 15 minutes.
- *sink*: `backend/app/rotas_auth.py:60` (entrar): The owner's next login, even with the correct password, gets HTTP 429 before the user lookup at line 65 and senha_confere at line 69.

**Evidence**

- `backend/app/rotas_auth.py:55`: tentativas.setdefault(dados.email, {...}) keys the lockout state only by the target email.
- `backend/app/rotas_auth.py:59`: The lock check runs before any credential verification, so a correct password cannot get past an active lock.
- `backend/app/rotas_auth.py:78`: The counter is reset only after a successful login, which cannot happen while the lock is active.
- `backend/app/modelos.py:74`: Login.v_email strips and lowercases, so case and whitespace variants share one counter: this helps the attacker and gives the owner no way around the lock.
- `backend/app/rotas_auth.py:29`: Cadastro returns 409 'E-mail já cadastrado' for existing addresses, which lets an attacker enumerate valid victim emails.
- `backend/app/config.py:15`: MAX_TENTATIVAS = 5 (with MINUTOS_BLOQUEIO = 15 at line 16) sets the attacker's cost at 5 requests per victim per 15 minutes.

**Blockers**

- No OS-enforced sandbox was available on this host, so no target code was executed and the 429 for the owner's correct password was not observed locally.
- RNF07 (docs/02-requisitos-nao-funcionais.md:20) prescribes a 15-minute block after 5 wrong passwords; whether a third party may trigger that block against someone else's account is an owner policy decision.
- The documented deployment is a single process (README.md:118, uvicorn --reload). Whether a real deployment adds an upstream proxy or rate limiter with a per-IP dimension, or runs multiple workers with separate in-memory dicts, is not visible in the repository.

**Resolution plan**

- **Local (sandboxed, dummy data):** In an isolated sandbox with no network, use the FastAPI TestClient with a disposable local Postgres fixture loaded from backend/database/schema.sql. Register a dummy user a@univille.br with password 'correta123' via POST /auth/cadastro and confirm it by GETting the returned link_confirmacao. Clear app.rotas_auth.tentativas. Send 5 POST /auth/login requests with {"email":"a@univille.br","senha":"errada000"} and expect 401 each time. Then send one POST /auth/login with {"email":"A@Univille.br ","senha":"correta123"} and expect 429. That shows a third party can lock out the owner and that the normalized variant does not bypass the lock. Stop after this single observation. Regression test for the fix: under the same sequence, the owner's correct password from a different requester context still succeeds, for example with a requester-scoped counter, a progressive delay instead of a hard block, or CAPTCHA/step-up.
- **Owner-observed (no audit traffic):** Without sending any audit traffic, the owner checks whether a reverse proxy or rate limiter in front of the API adds a per-IP or per-client limit, and how many uvicorn worker processes are configured. Neither is present in the repository.

## 5. The RNF07 attempt limit is a non-atomic check-then-increment, so concurrent guesses exceed 5 per window

**Fingerprint:** `caroville:rotas_auth:login-lockout-check-then-act-race`

POST /auth/login (entrar) is a sync route, so FastAPI runs it in the AnyIO threadpool (40 worker tokens by default). It reads the per-email lock state at rotas_auth.py:58, runs a bcrypt checkpw at line 69 (the pyca bcrypt binding releases the GIL while hashing), and records the failure only at lines 70-72. Nothing is reserved before verification, and the dict at line 17 has no lock. N concurrent wrong-password requests for one account can therefore all pass line 58 before any of them increments erros. Up to about one threadpool's worth of real password guesses per process can then be evaluated in a 15-minute window instead of MAX_TENTATIVAS=5 (config.py:15-16). Each additional worker process keeps its own dict, which multiplies this further. Email normalization is consistent (Login.v_email and Cadastro.v_email both strip and lowercase, modelos.py:42,74), so this is not a case-variant bypass. The effect weakens the brute-force bound for a chosen account rather than bypassing authentication directly. Passwords are at least 8 characters and bcrypt cost is 10, so the realistic impact is low.

**Claimed root cause:** The lockout decision (rotas_auth.py:58) and the failure accounting (rotas_auth.py:70-72) are separate, unsynchronized steps around the slow bcrypt verification (rotas_auth.py:69, seguranca.py:21). No attempt is reserved atomically before verification, and the counter lives in an unlocked, per-process module dict (rotas_auth.py:17).

**Trace**

- *entrypoint*: `backend/app/rotas_auth.py:54` (entrar): Anonymous POST /auth/login (a sync def, run in the threadpool); the attacker sends N concurrent requests with the victim's email and different wrong passwords.
- *propagation*: `backend/app/rotas_auth.py:58` (entrar): Each concurrent request reads the shared controle entry and sees bloqueado_ate as None because no failure has been recorded yet.
- *propagation*: `backend/app/rotas_auth.py:69` (entrar): Each request runs senha_confere (bcrypt.checkpw, seguranca.py:21) against the victim's real hash, so every request is a genuine password guess.
- *sink*: `backend/app/rotas_auth.py:70` (entrar): The failure is counted (an unsynchronized +=) only after verification, and the lock is set at lines 71-72, after more than MAX_TENTATIVAS guesses may already have been evaluated.

**Evidence**

- `backend/app/rotas_auth.py:17`: Module-level tentativas dict, per process, with no threading lock.
- `backend/app/rotas_auth.py:58`: The lock check happens before verification and reserves no attempt.
- `backend/app/seguranca.py:21`: bcrypt.checkpw is the slow step that widens the race window.
- `backend/app/rotas_auth.py:70`: The non-atomic increment happens after bcrypt; the lock is set at line 72 only once erros >= MAX_TENTATIVAS.
- `backend/app/config.py:15`: MAX_TENTATIVAS = 5 and MINUTOS_BLOQUEIO = 15 (line 16) are the RNF07 bound that the race exceeds.
- `backend/app/modelos.py:74`: The login email is stripped and lowercased the same way as at registration, so an account always maps to one dict key; the race does not depend on key variants.

**Blockers**

- No OS-enforced sandbox was available on this Windows host, so no target code was executed and the concurrent schedule, which is the decisive evidence for the bypass count, was not observed.
- The number of extra guesses per window depends on the deployed uvicorn worker count and threadpool size, which are not in the repository; README.md:118 shows only a local single-process dev command.

**Resolution plan**

- **Local (sandboxed, dummy data):** Only in an approved sandbox (no network, scratch-only writes, low time limits): import app.main:app and set app.dependency_overrides[app.db.get_db] to a generator that yields a fake connection whose execute(...).fetchone() returns {'id': 1, 'senha_hash': '<dummy bcrypt hash>', 'email_verificado': True}, so no Postgres is needed. Clear app.rotas_auth.tentativas. Monkeypatch app.rotas_auth.senha_confere with a stub that increments a thread-safe counter, waits on threading.Barrier(10, timeout=5) and returns False. Fire 10 concurrent TestClient POST /auth/login requests with {'email':'dummy@univille.br','senha':'wrongpass'} from a ThreadPoolExecutor(10), then send one more request. Vulnerable result: the stub counter is 10 (more than 5) and only the final request gets 429. Regression test with the fix applied: the counter must be at most MAX_TENTATIVAS, and the excess requests must get 429 without reaching senha_confere, for example by reserving or incrementing the attempt under a threading.Lock (or an atomic DB or shared-store counter) before verification.
- **Owner-observed (no audit traffic):** Without sending any audit traffic, the owner reports the deployed uvicorn/gunicorn worker count and any custom AnyIO threadpool limit. Each worker process holds its own tentativas dict, which multiplies the effective per-window limit.

## 6. Unauthenticated login requests permanently add arbitrarily long email keys to the in-memory tentativas dict

**Fingerprint:** `caroville:rotas_auth:tentativas-unbounded-email-keys`

Every POST /auth/login runs tentativas.setdefault(dados.email, {...}) (backend/app/rotas_auth.py:55) before the user lookup and before any check. Login.email (backend/app/modelos.py:67-74) is only stripped and lowercased; unlike Cadastro.email it has no length, format or domain check, while schema.sql:13 caps stored emails at VARCHAR(150). Nothing in backend/app ever deletes a key: lines 63 and 78 only reset the values, and there is no TTL, LRU or size cap. For an email with no account, usuario is None at line 69, so bcrypt is skipped and each request costs one parameterized SELECT and returns 401. An anonymous client can therefore keep growing the API process's memory by sending distinct, arbitrarily long email strings. Memory retained grows roughly linearly with the bytes sent (the key plus a small dict per entry, with no amplification), lasts until the process restarts, and is shared by every user of that process. Whether this reaches meaningful exhaustion depends on request-body limits, per-IP rate limiting and process memory limits, none of which are in the repository; ADR-003 describes a local-only deployment.

**Claimed root cause:** Per-identifier lockout state is created for unvalidated, attacker-chosen login identifiers (backend/app/rotas_auth.py:55; backend/app/modelos.py:71-74) with no cap on the number of entries, no key-length bound and no eviction.

**Trace**

- *entrypoint*: `backend/app/rotas_auth.py:53` (entrar): Unauthenticated POST /auth/login route with no auth dependency, only get_db; JSON body {"email": <unique arbitrary string>, "senha": <any string>}.
- *propagation*: `backend/app/modelos.py:74` (Login.v_email): The email only gets strip() and lower(), with no length, format or domain bound (unlike Cadastro.v_email at modelos.py:39-47).
- *sink*: `backend/app/rotas_auth.py:55` (entrar): tentativas.setdefault inserts the attacker-chosen key into the module-level dict (line 17) before the DB lookup, and the entry stays for the life of the process.

**Evidence**

- `backend/app/rotas_auth.py:17`: tentativas is a module-level, process-global dict with no size bound.
- `backend/app/rotas_auth.py:55`: An entry is inserted unconditionally for any submitted email, before the lookup at lines 65-67.
- `backend/app/rotas_auth.py:69`: For a non-existent email, usuario is None and the or short-circuits, so bcrypt senha_confere is never called; the cost per request is one SELECT.
- `backend/app/rotas_auth.py:78`: A successful login only resets the values (as does line 63 when a lock expires); no code anywhere deletes a key.
- `backend/app/modelos.py:71`: The Login.email validator has no maximum length, whereas backend/database/schema.sql:13 limits stored emails to VARCHAR(150).
- `backend/app/main.py:12`: The only middleware is CORS; the app configures no body-size limit, rate limit or other request gate.

**Blockers**

- No OS-enforced sandbox was available on this host, so no target code was run and key retention could not be observed locally.
- Request-body size limits (in the uvicorn/ASGI server or any reverse proxy), per-IP rate limiting on /auth/login, the worker count and restart policy, and process memory limits are deployment facts not present in the repository, and they decide whether the growth has meaningful shared availability impact.
- Availability impact must not be stress-tested; validation is limited to observing that keys are retained.

**Resolution plan**

- **Local (sandboxed, dummy data):** In an isolated sandbox with no network, scratch-only writes and strict memory and time limits: import app.main and use FastAPI TestClient with the get_db dependency overridden by a stub whose execute(...).fetchone() returns None, so no Postgres is needed. Clear app.rotas_auth.tentativas, then POST /auth/login 1,000 times with distinct emails of about 1 KB each (for example 'x'*1000 + f'{i}@a') and senha 'x'. Assert that every response is 401, len(tentativas) == 1000, and the longest key is at least 1000 characters. Make one more request to a different path and re-assert that the count has not shrunk. Stop there, with no load or memory stress. Regression test after the fix: an email over 150 characters is rejected with 422 before any state is touched, and unknown emails do not create permanent entries (or the dict stays within a fixed cap via TTL/LRU eviction).
- **Owner-observed (no audit traffic):** Without sending any test traffic, the owner reports whether the API runs behind a reverse proxy or ASGI server configuration that enforces a request-body size limit and a per-IP rate limit on POST /auth/login, how many worker processes run, and whether a supervisor restart policy or a memory limit (container or cgroup) applies to the API process.

