"""Caroville - API (FastAPI). Documentação automática em /docs."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import rotas_auth, rotas_caronas, rotas_perfil

app = FastAPI(title="Caroville API", version="0.1.0")

# Permite o frontend (Vite, porta 5173) chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"mensagem": "Caroville API no ar. Veja a documentação em /docs"}
