"""Apoio comum dos testes.

Os testes usam o banco configurado no .env (DATABASE_URL), que precisa ter o
schema.sql e o seed.sql carregados (os locais vêm do seed). Cada teste cria os
próprios usuários e caronas, e tudo isso é apagado ao final.
"""
import random
import string
import uuid
from datetime import datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.config import DATABASE_URL
from app.main import app

PREFIXO = "teste."
SENHA = "senha1234"


def sql(consulta, parametros=()):
    """Executa um SQL direto no banco (para conferir ou ajustar dados)."""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        cur = conn.execute(consulta, parametros)
        return cur.fetchall() if cur.description else None


def iso(quando):
    return quando.replace(microsecond=0).isoformat()


def agora():
    return datetime.now()


def placa():
    """Placa Mercosul aleatória (a placa é única no banco). Começa com Z para não bater com o seed."""
    letras, digitos = string.ascii_uppercase, string.digits
    return ("Z" + "".join(random.choices(letras, k=2)) + random.choice(digitos)
            + random.choice(letras) + "".join(random.choices(digitos, k=2)))


class Usuario:
    def __init__(self, cliente, email, id, token):
        self.cliente, self.email, self.id = cliente, email, id
        self.headers = {"Authorization": f"Bearer {token}"}

    def get(self, url, **kw):
        return self.cliente.get(url, headers=self.headers, **kw)

    def post(self, url, **kw):
        return self.cliente.post(url, headers=self.headers, **kw)

    def put(self, url, **kw):
        return self.cliente.put(url, headers=self.headers, **kw)

    def delete(self, url, **kw):
        return self.cliente.delete(url, headers=self.headers, **kw)


@pytest.fixture(scope="session")
def cliente():
    with TestClient(app) as c:
        yield c
    # limpeza: remove tudo que os testes criaram
    filtro = PREFIXO + "%"
    sql("""DELETE FROM solicitacao WHERE passageiro_id IN (SELECT id FROM usuario WHERE email LIKE %s)
           OR carona_id IN (SELECT id FROM carona WHERE motorista_id IN
                            (SELECT id FROM usuario WHERE email LIKE %s))""", (filtro, filtro))
    sql("DELETE FROM carona WHERE motorista_id IN (SELECT id FROM usuario WHERE email LIKE %s)", (filtro,))
    sql("DELETE FROM usuario WHERE email LIKE %s", (filtro,))


@pytest.fixture(scope="session")
def locais(cliente):
    """Ids dos locais do seed, pelo nome."""
    return {l["nome"]: l["id"] for l in cliente.get("/locais").json()}


@pytest.fixture
def campus(locais):
    return locais["Campus Univille"]


@pytest.fixture
def bairro(locais):
    return locais["Costa e Silva"]


@pytest.fixture
def outro_bairro(locais):
    return locais["Boa Vista"]


def _cadastrar(cliente, com_veiculo):
    email = f"{PREFIXO}{uuid.uuid4().hex[:8]}@univille.br"
    r = cliente.post("/auth/cadastro", json={
        "nome": "Usuário Teste", "email": email, "curso": "Ciência da Computação",
        "telefone": "(47) 99999-0000", "senha": SENHA,
    })
    assert r.status_code == 201, r.text
    cliente.get(r.json()["link_confirmacao"].replace("http://localhost:8000", ""))
    token = cliente.post("/auth/login", json={"email": email, "senha": SENHA}).json()["token"]
    usuario_id = sql("SELECT id FROM usuario WHERE email = %s", (email,))[0][0]
    u = Usuario(cliente, email, usuario_id, token)
    if com_veiculo:
        r = u.post("/veiculos", json={"modelo": "Fiat Argo", "cor": "Prata", "placa": placa(), "lugares": 4})
        assert r.status_code == 201, r.text
    return u


@pytest.fixture
def novo_usuario(cliente):
    """Fábrica de usuários já confirmados e logados."""
    return lambda com_veiculo=False: _cadastrar(cliente, com_veiculo)


@pytest.fixture
def motorista(novo_usuario):
    return novo_usuario(com_veiculo=True)


@pytest.fixture
def passageiro(novo_usuario):
    return novo_usuario()


@pytest.fixture
def passageiro2(novo_usuario):
    return novo_usuario()


@pytest.fixture
def criar_carona(campus, bairro):
    """Fábrica de caronas (padrão: Costa e Silva -> Campus, daqui a 1 dia, 3 vagas)."""
    def _criar(motorista, quando=None, vagas=3, origem=None, destino=None):
        quando = quando or agora() + timedelta(days=1)
        r = motorista.post("/caronas", json={
            "origem_id": origem or bairro, "destino_id": destino or campus,
            "saida_em": iso(quando), "vagas_total": vagas, "ponto_encontro": "Praça central",
        })
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _criar
