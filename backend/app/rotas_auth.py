"""US01 - Cadastro e login (RF01, RF02, RF03)."""
import threading
from datetime import datetime, timedelta

import jwt
import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request

from app import config
from app.config import MAX_TENTATIVAS, MINUTOS_BLOQUEIO
from app.db import get_db
from app.modelos import Cadastro, Login
from app.seguranca import HASH_FALSO, criar_token, gerar_hash, ler_token, senha_confere

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# RNF07: controle de tentativas guardado na memória do servidor (simples para o MVP)
# formato: {(ip, email): {"erros": 2, "bloqueado_ate": datetime ou None, "ultima": datetime}}
# VULN-04: a chave inclui o IP, então um estranho não bloqueia a conta de outra pessoa
tentativas: dict = {}
MAX_REGISTROS = 5000
trava = threading.Lock()  # VULN-13: protege o contador quando chegam várias requisições juntas


def _limpar_tentativas():
    """Apaga registros parados há mais que o tempo de bloqueio (a memória não cresce sem fim)."""
    limite = datetime.now() - timedelta(minutes=MINUTOS_BLOQUEIO)
    for chave in [k for k, v in tentativas.items() if v["ultima"] < limite]:
        del tentativas[chave]


@router.post("/cadastro", status_code=201)
def cadastrar(dados: Cadastro, db=Depends(get_db)):
    try:
        usuario = db.execute(
            """INSERT INTO usuario (nome, email, senha_hash, curso, telefone)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (dados.nome, dados.email, gerar_hash(dados.senha), dados.curso, dados.telefone),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "E-mail já cadastrado")

    # RF02: no MVP não há envio de e-mail; o link é mostrado no terminal.
    # VULN-01: só vai na resposta da API se MODO_DEMO=true (senão qualquer um confirmaria e-mails alheios)
    token = criar_token({"sub": str(usuario["id"]), "tipo": "confirmar_email"}, minutos=60 * 24)
    link = f"http://localhost:8000/auth/confirmar-email?token={token}"
    print(f"[E-MAIL SIMULADO] Para {dados.email}: confirme sua conta em {link}")
    resposta = {"mensagem": "Conta criada! Confirme seu e-mail para entrar."}
    if config.MODO_DEMO:
        resposta["link_confirmacao"] = link
    return resposta


@router.get("/confirmar-email")
def confirmar_email(token: str, db=Depends(get_db)):
    try:
        dados = ler_token(token)
    except jwt.PyJWTError:
        raise HTTPException(400, "Link de confirmação inválido ou expirado")
    if dados.get("tipo") != "confirmar_email":
        raise HTTPException(400, "Link de confirmação inválido ou expirado")
    db.execute("UPDATE usuario SET email_verificado = TRUE WHERE id = %s", (dados["sub"],))
    return {"mensagem": "E-mail confirmado! Agora você já pode entrar."}


@router.post("/login")
def entrar(dados: Login, request: Request, db=Depends(get_db)):
    if len(dados.email) > 150:  # VULN-04: não guarda e-mails gigantes na memória
        raise HTTPException(401, "E-mail ou senha incorretos")

    # VULN-13: a tentativa é reservada ANTES de conferir a senha, dentro de uma trava.
    # Assim, várias requisições simultâneas não passam de MAX_TENTATIVAS.
    with trava:
        if len(tentativas) > MAX_REGISTROS:
            _limpar_tentativas()
        chave = (request.client.host if request.client else "?", dados.email)
        controle = tentativas.setdefault(chave, {"erros": 0, "bloqueado_ate": None})
        controle["ultima"] = datetime.now()

        # RNF07: login bloqueado
        if controle["bloqueado_ate"]:
            if datetime.now() < controle["bloqueado_ate"]:
                raise HTTPException(
                    429, f"Muitas tentativas. Login bloqueado por {MINUTOS_BLOQUEIO} minutos."
                )
            controle.update(erros=0, bloqueado_ate=None)

        controle["erros"] += 1  # reserva a tentativa
        if controle["erros"] > MAX_TENTATIVAS:
            controle["bloqueado_ate"] = datetime.now() + timedelta(minutes=MINUTOS_BLOQUEIO)
            raise HTTPException(
                429, f"Muitas tentativas. Login bloqueado por {MINUTOS_BLOQUEIO} minutos."
            )

    usuario = db.execute(
        "SELECT id, senha_hash, email_verificado FROM usuario WHERE email = %s", (dados.email,)
    ).fetchone()

    # VULN-05: sempre gasta o tempo de um bcrypt, exista o e-mail ou não
    hash_comparado = usuario["senha_hash"] if usuario else HASH_FALSO
    senha_ok = senha_confere(dados.senha, hash_comparado)
    if usuario is None or not senha_ok:
        with trava:
            if controle["erros"] >= MAX_TENTATIVAS:
                controle["bloqueado_ate"] = datetime.now() + timedelta(minutes=MINUTOS_BLOQUEIO)
        raise HTTPException(401, "E-mail ou senha incorretos")

    if not usuario["email_verificado"]:
        raise HTTPException(403, "Confirme seu e-mail")

    with trava:
        controle.update(erros=0, bloqueado_ate=None)
    return {"token": criar_token({"sub": str(usuario["id"]), "tipo": "acesso"})}
