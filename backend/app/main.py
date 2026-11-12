"""Caroville - API (FastAPI). Documentação automática em /docs."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import rotas_auth, rotas_caronas, rotas_perfil
from app.config import MODO_DEMO

# VULN-07: /docs, /redoc e /openapi.json só existem no modo demonstração
app = FastAPI(
    title="Caroville API",
    version="0.1.0",
    docs_url="/docs" if MODO_DEMO else None,
    redoc_url="/redoc" if MODO_DEMO else None,
    openapi_url="/openapi.json" if MODO_DEMO else None,
)

# Permite o frontend (Vite, porta 5173) chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # VULN-09: só o que a API usa
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def cabecalhos_de_seguranca(request: Request, chamar_proximo):
    """VULN-08: cabeçalhos de segurança em todas as respostas."""
    resposta = await chamar_proximo(request)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@app.exception_handler(RequestValidationError)
async def erro_de_validacao(request: Request, erro: RequestValidationError):
    """Devolve só a primeira mensagem de erro, em português, no campo 'detail'."""
    primeiro = erro.errors()[0]
    mensagem = str(primeiro.get("msg", "Dados inválidos"))
    if primeiro["type"] == "missing":
        mensagem = "Preencha todos os campos"
    elif primeiro["type"] in ("int_parsing", "int_type"):
        mensagem = "Informe um número válido"
    elif primeiro["type"].startswith(("datetime", "date_")):
        mensagem = "Data ou horário inválido"
    mensagem = mensagem.removeprefix("Value error, ")
    return JSONResponse(status_code=422, content={"detail": mensagem})


app.include_router(rotas_auth.router)
app.include_router(rotas_perfil.router)
app.include_router(rotas_caronas.router)


@app.get("/", tags=["Geral"])
def raiz():
    return {"mensagem": "Caroville API no ar"}
