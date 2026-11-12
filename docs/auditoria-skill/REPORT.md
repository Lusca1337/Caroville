# Caroville: Security Audit Report (run 1)

## 1. Run scope and limits

| | |
|---|---|
| **Target** | `Lusca1337/Caroville` at commit `7a4169a`, **dirty worktree** (uncommitted `rotas_caronas.py` and docs changes; untracked `frontend/`, `backend/tests/`) |
| **Profile** | `quick`: one hunter wave plus one final coverage critic. **This is a partial pass, not exhaustive coverage.** |
| **Scope** | `backend/app`, `backend/database`, `backend/tests`, `backend/requirements.txt`, `backend/.env.example`, `frontend/src`, frontend config/manifests, `.gitignore`, `docs`, `README.md`. Out of scope: `backend/venv`, `node_modules` (read only as evidence for the Vite lead), `.agents/`, `.claude/`, and `backend/.env` (its values were deliberately not read). |
| **Budget** | None set. Spent 12 agents: 3 hunters, 1 critic, 8 verifiers. Reconnaissance was done directly by the parent (see deviations). |
| **Execution** | Sandboxed-source-and-local-only policy. **No target code was executed.** This Windows host cannot provide the OS-enforced sandbox the method requires (no network, empty environment, read-only target, resource limits) or race-safe artifact promotion. All evidence is source review. Because a `confirmed` verdict requires a bounded local observed result, **no record could reach `confirmed` in this run.** Source-complete leads are reported as `needs_validation`, each with an exact local test you can run. |
| **Prior runs** | None. This is the first ledger for this repository. |

**Deviations from the skill workflow, recorded for transparency:**
- Reconnaissance roles 1a–1d were performed by the parent reading the small codebase (~940 backend LOC plus the SPA) instead of four delegated agents.
- The skill's validators refuse to open any file on Windows because `O_NOFOLLOW` is missing. The parent-written run files were validated through a wrapper that calls the validators' unchanged `validateDocument()` logic. Both validators pass.

## 2. Security posture

Most of the core authorization is solid:
- Every SQL statement is parameterized.
- Driver and passenger ownership checks run on DB-loaded rows before any write.
- Seat accounting is serialized with row locks and backed by CHECK constraints.
- JWTs pin HS256 and separate access tokens from confirmation tokens by `tipo`.
- The RN10 phone-disclosure rule holds on every path.
- React escaping and the absence of HTML sinks rule out DOM XSS.

The weak points are the **identity perimeter** and the **development toolchain**:
- Email ownership is never proven because the confirmation token is returned to the registrant.
- The JWT key falls back to a public literal.
- The login lockout can be turned against victims and raced.
- The pinned Vite dev server version is publicly known to let other websites read local files.

## 3. Confirmed findings

**None.** The missing sandbox prevented confirmation (see §1). This does not mean the code is free of vulnerabilities: six source-complete leads below await a local run.

## 4. Confirmed finding details

None.

## 5. NEEDS VALIDATION (no severity assigned; not confirmed vulnerabilities)

They are listed in suggested triage order. Full traces and plans are in [NEEDS-VALIDATION.md](NEEDS-VALIDATION.md).

| # | Lead | Repository trace | Exact blocker | Bounded local next step | Owner-observed check |
|---|---|---|---|---|---|
| 1 | **Registration returns the email-confirmation token.** Anyone can create a verified account for any unregistered `@univille.br` address, or squat a real student's address. | `backend/app/rotas_auth.py:21 → :32 → :37 → :49 → :79` | No sandbox; whether any instance is reachable beyond the developer | TestClient: cadastro, then GET `link_confirmacao`, then login returns 200 | Is any instance reachable by others? If yes, send the token only by email |
| 2 | **JWT signing key falls back to a public literal** (`chave-apenas-para-desenvolvimento`, or the `.env.example` placeholder). With either value anyone can forge a token for any user. | `backend/app/config.py:8`, `backend/app/seguranca.py:26,30,45,47` | No sandbox; deployed key value; reachability | Start with `SECRET_KEY` unset, mint a token with the literal, GET `/perfil` returns 200 | Confirm `.env` sets a random key of 32+ bytes that is neither literal |
| 3 | **Vite 5.4.11 dev server allows cross-origin reads of arbitrary local files** (CVE-2025-24010, CVE-2025-30208), including `backend/.env`. | `frontend/package.json:18`, `frontend/vite.config.js:7`, `node_modules/vite/.../dep-CB_7IfJ-.js:63087,61864,51799,20316` | No sandbox; browser Private/Local Network Access behavior | Loopback-only sandbox: cross-origin fetch of `/@fs/<canary>?import&raw??` returns the content | — (upgrade to vite ≥ 5.4.19 resolves it) |
| 4 | **Login lockout can be weaponized:** 5 bad passwords every 15 min keep any user locked out, even with the correct password. | `backend/app/rotas_auth.py:54 → :55 → :72 → :60` | No sandbox; RNF07 policy intent; upstream per-IP limits | TestClient: 5 wrong logins, then the correct login returns 429 | Is there a proxy or rate limiter with a per-IP dimension? |
| 5 | **The lockout check-then-increment is non-atomic,** so concurrent guesses exceed 5 per window. | `backend/app/rotas_auth.py:54 → :58 → :69 → :70` | No sandbox; worker count and threadpool size | Barrier-stubbed `senha_confere` with 10 concurrent logins; counter > 5 | uvicorn worker count and threadpool limit |
| 6 | **The unauthenticated login path permanently stores arbitrarily long email keys** in the `tentativas` dict, so memory grows without bound. | `backend/app/rotas_auth.py:53`, `backend/app/modelos.py:74`, `backend/app/rotas_auth.py:55` | No sandbox; body-size, rate and memory limits upstream | Stubbed DB: 1,000 distinct 1 KB emails give `len(tentativas)==1000` (no stress) | Proxy body and rate limits, worker memory limits |

**Smallest fixes, if you choose to act without waiting for validation:**
1. Remove `link_confirmacao` from the cadastro response, or gate it behind an off-by-default dev flag.
2. Fail startup when `SECRET_KEY` is missing, equals either literal, or is shorter than 32 bytes.
3. Upgrade `vite` to the latest 5.4.x (≥ 5.4.19).
4. Scope the lockout to requester plus account, or use progressive delay.
5. Reserve the attempt under a lock before running bcrypt.
6. Cap `Login.email` at 150 characters and only track existing accounts, or evict entries with TTL/LRU.

## 6. Hardening notes and positive patterns

**Hardening (not findings):**
- Passwords over 72 bytes probably cause a 500, because bcrypt 5.x raises and there is no max-length validator on `Cadastro.senha` or `Login.senha`.
- Login timing differs for existing and non-existing emails (bcrypt is skipped for unknown ones). Cadastro's 409 already reveals which accounts exist.
- `POST /auth/cadastro` runs bcrypt on every unauthenticated request with no rate limit.
- The confirmation JWT is printed to stdout and placed in a query string.
- Tokens have no `iss` or `aud`. Add them if the key is ever shared between services.
- The RN12 overlap check locks only the accepting ride, so two drivers accepting the same passenger concurrently can create overlapping CONFIRMADA requests. Lock the passenger row.
- A concurrent duplicate seat request raises an unhandled `UniqueViolation` (500). Map it to 409.
- `atualizar_status_automaticos` runs table-wide UPDATEs inside every ride request. Concurrent requests can contend or deadlock. Use a scheduled job or an advisory lock.
- `cancelar_solicitacao` locks the ride before checking that the caller owns the request.
- `oferecer_carona` does not compare `vagas_total` with the vehicle's `lugares`.
- `_telefone` validates the digit count but stores the raw string. Store only the digits.
- 404 and 403 responses differ, which reveals whether an id exists. Ids are sequential anyway.
- Profile names may contain CR/LF/ESC characters, which reach the stdout "email" log. Reject or escape control characters before real email or logging is added. This was verified as rejected as a vulnerability.
- The SPA concatenates decoded `:id` route params into API paths without encoding, so a crafted link can redirect the victim's GET requests to another API path. There is no mutation impact today. Validate the id as an integer.
- The root `.gitignore` is untracked, and `__pycache__` was committed.
- `backend/requirements.txt` is completely unpinned and has no lockfile.
- `seed.sql` creates verified users with the password `senha1234`, and `DATABASE_URL` defaults to `postgres:postgres`.
- FastAPI `/docs`, `/redoc` and `/openapi.json` are unauthenticated.
- Google Fonts is loaded from a third party.

**Positive patterns:**
- Parameterized SQL throughout.
- Ownership checks done in the same statement (`WHERE id=%s AND usuario_id=%s`).
- `FOR UPDATE` row locks on every seat-changing path.
- Database CHECK constraints and a partial unique index back up the business rules.
- Pinned `algorithms=["HS256"]`, `tipo` role separation, and `exp` on every token.
- Pydantic models whitelist fields, so mass assignment is not possible.
- Exact-origin CORS allowlist with no credentials.
- No HTML sinks in the SPA.
- Consistent email normalization.

## 7. Coverage summary (from `coverage-ledger.json`)

| State | Units |
|---|---|
| covered | 6: JWT/crypto, rides access control, rides business logic, profile/vehicle access control, frontend/client-side, wildcard |
| candidate | 4: auth business logic (4 leads), injection (1 rejected), rides data leakage (1 rejected), obvious things (2 leads) |
| blocked | 0 |
| deferred | 1: **resource exhaustion on authenticated routes** |

- **Final critic result:** one accepted gap. The original ledger excluded resource exhaustion on authenticated routes with a reason the source does not support. The routes have unpaginated `fetchall()` lists (`buscar_caronas`, `/minhas/*`, `/caronas/{id}/solicitacoes`), no per-user caps on `POST /caronas` or `POST /veiculos`, and table-wide UPDATEs in `db_atualizado` on every ride request. Lead #1 also makes the number of accounts unbounded. Per the quick profile this unit is **deferred (`quick_profile_final_critic`)** and was not hunted. **Make it the first unit of the next run.**
- **Rejected records (2):** `ver_carona` returns ride details by id, but only data already published to every user, with the phone still gated. Console notification-line forging has only a developer-terminal reader. These are kept so future runs do not re-raise them without new evidence.
- **Excluded companion domains**, with source reasons in the ledger: AI/LLM, memory safety, desktop/IPC, protocols/messaging, cloud/deployment, supply-chain/release, data isolation/lifecycle. CSRF is excluded because authentication is a header bearer token, not an ambient cookie.
- **Next run:** a `standard` profile on a Linux/macOS host with a real sandbox can validate leads 1–6 locally and hunt the deferred unit.
