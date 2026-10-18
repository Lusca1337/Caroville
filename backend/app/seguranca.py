"""Senha (bcrypt), token JWT e usuário logado."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import SECRET_KEY, TOKEN_MINUTOS
from app.db import get_db

ALGORITMO = "HS256"
esquema = HTTPBearer(auto_error=False)


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(10)).decode()


def senha_confere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def criar_token(dados: dict, minutos: int = TOKEN_MINUTOS) -> str:
    corpo = dict(dados, exp=datetime.now(timezone.utc) + timedelta(minutes=minutos))
    return jwt.encode(corpo, SECRET_KEY, algorithm=ALGORITMO)


def ler_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])


def usuario_logado(
    credenciais: HTTPAuthorizationCredentials = Depends(esquema),
    db=Depends(get_db),
) -> dict:
    """Dependência: devolve o usuário do token ou responde 401."""
    erro = HTTPException(401, "Sessão inválida ou expirada. Faça login novamente.")
    if credenciais is None:
        raise erro
    try:
        dados = ler_token(credenciais.credentials)
    except jwt.PyJWTError:
        raise erro
    if dados.get("tipo") != "acesso":
        raise erro
    usuario = db.execute(
        "SELECT id, nome, email, curso, telefone, email_verificado FROM usuario WHERE id = %s",
        (dados.get("sub"),),
    ).fetchone()
    if usuario is None:
        raise erro
    return usuario
