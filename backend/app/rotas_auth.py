"""US01 - Cadastro e login (RF01, RF02, RF03)."""
from datetime import datetime, timedelta

import jwt
import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.config import MAX_TENTATIVAS, MINUTOS_BLOQUEIO
from app.db import get_db
from app.modelos import Cadastro, Login
from app.seguranca import criar_token, gerar_hash, ler_token, senha_confere

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# RNF07: controle de tentativas guardado na memória do servidor (simples para o MVP)
# formato: {email: {"erros": 2, "bloqueado_ate": datetime ou None}}
tentativas: dict = {}


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

    # RF02: no MVP não há envio de e-mail; o link é mostrado no terminal e devolvido na resposta
    token = criar_token({"sub": str(usuario["id"]), "tipo": "confirmar_email"}, minutos=60 * 24)
    link = f"http://localhost:8000/auth/confirmar-email?token={token}"
    print(f"[E-MAIL SIMULADO] Para {dados.email}: confirme sua conta em {link}")
    return {
        "mensagem": "Conta criada! Confirme seu e-mail para entrar.",
        "link_confirmacao": link,
    }


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
def entrar(dados: Login, db=Depends(get_db)):
    controle = tentativas.setdefault(dados.email, {"erros": 0, "bloqueado_ate": None})

    # RNF07: login bloqueado
    if controle["bloqueado_ate"]:
        if datetime.now() < controle["bloqueado_ate"]:
            raise HTTPException(
                429, f"Muitas tentativas. Login bloqueado por {MINUTOS_BLOQUEIO} minutos."
            )
        controle.update(erros=0, bloqueado_ate=None)

    usuario = db.execute(
        "SELECT id, senha_hash, email_verificado FROM usuario WHERE email = %s", (dados.email,)
    ).fetchone()

    if usuario is None or not senha_confere(dados.senha, usuario["senha_hash"]):
        controle["erros"] += 1
        if controle["erros"] >= MAX_TENTATIVAS:
            controle["bloqueado_ate"] = datetime.now() + timedelta(minutes=MINUTOS_BLOQUEIO)
        raise HTTPException(401, "E-mail ou senha incorretos")

    if not usuario["email_verificado"]:
        raise HTTPException(403, "Confirme seu e-mail")

    controle.update(erros=0, bloqueado_ate=None)
    return {"token": criar_token({"sub": str(usuario["id"]), "tipo": "acesso"})}
