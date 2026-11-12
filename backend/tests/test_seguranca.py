"""Testes das correções de segurança (relatório em docs/relatorio-seguranca.md).

Cada teste leva o ID da vulnerabilidade (VULN-xx) que ele protege.
"""
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import config, rotas_auth
from tests.conftest import SENHA, sql


def _dados(**mudar):
    d = {"nome": "Teste Seg", "email": f"teste.{uuid.uuid4().hex[:8]}@univille.br",
         "curso": "Direito", "telefone": "(47) 99999-0000", "senha": SENHA}
    d.update(mudar)
    return d


# VULN-01 ------------------------------------------------------------------
def test_cadastro_nao_devolve_link_fora_do_modo_demo(cliente, monkeypatch):
    monkeypatch.setattr(config, "MODO_DEMO", False)
    r = cliente.post("/auth/cadastro", json=_dados())
    assert r.status_code == 201
    assert "link_confirmacao" not in r.json()


def test_cadastro_devolve_link_no_modo_demo(cliente, monkeypatch):
    monkeypatch.setattr(config, "MODO_DEMO", True)
    r = cliente.post("/auth/cadastro", json=_dados())
    assert "link_confirmacao" in r.json()


# VULN-02 ------------------------------------------------------------------
def _config_com(env):
    """Importa app.config num processo novo com as variáveis dadas."""
    e = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "DATABASE_URL")}
    e.update(env)
    return subprocess.run([sys.executable, "-c", "import app.config"], env=e,
                          capture_output=True, text=True, cwd=os.getcwd())


@pytest.mark.parametrize("chave", ["", "curta", "chave-apenas-para-desenvolvimento",
                                   "troque-esta-chave-por-um-texto-grande-e-aleatorio"])
def test_servidor_recusa_chave_fraca(chave):
    r = _config_com({"DATABASE_URL": "postgresql://x", "SECRET_KEY": chave, "PYTHON_DOTENV_DISABLED": "1"})
    assert r.returncode != 0 and "SECRET_KEY" in r.stderr


def test_token_forjado_com_chave_antiga_e_recusado(cliente, passageiro):
    forjado = jwt.encode({"sub": str(passageiro.id), "tipo": "acesso",
                          "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                         "chave-apenas-para-desenvolvimento", algorithm="HS256")
    r = cliente.get("/perfil", headers={"Authorization": f"Bearer {forjado}"})
    assert r.status_code == 401


def test_token_sem_expiracao_e_recusado(cliente, passageiro):
    sem_exp = jwt.encode({"sub": str(passageiro.id), "tipo": "acesso"}, config.SECRET_KEY, algorithm="HS256")
    assert cliente.get("/perfil", headers={"Authorization": f"Bearer {sem_exp}"}).status_code == 401


def test_token_alg_none_e_recusado(cliente, passageiro):
    token = jwt.encode({"sub": str(passageiro.id), "tipo": "acesso"}, None, algorithm="none")
    assert cliente.get("/perfil", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# VULN-03 ------------------------------------------------------------------
def test_servidor_recusa_sem_database_url():
    r = _config_com({"SECRET_KEY": "x" * 40, "PYTHON_DOTENV_DISABLED": "1"})
    assert r.returncode != 0 and "DATABASE_URL" in r.stderr


# VULN-04 ------------------------------------------------------------------
def test_bloqueio_nao_vale_para_outro_ip(cliente, passageiro):
    """Quem erra a senha de outra pessoa (de outro IP) não a impede de entrar."""
    from fastapi.testclient import TestClient
    from app.main import app
    for _ in range(5):
        cliente.post("/auth/login", json={"email": passageiro.email, "senha": "errada1234"})
    # o IP do atacante foi bloqueado...
    assert cliente.post("/auth/login", json={"email": passageiro.email, "senha": SENHA}).status_code == 429
    # ...mas o dono da conta, de outro IP, entra normalmente
    dono = TestClient(app, client=("10.0.0.9", 5000))
    assert dono.post("/auth/login", json={"email": passageiro.email, "senha": SENHA}).status_code == 200


def test_memoria_de_tentativas_e_limpa(cliente):
    antigo = datetime.now() - timedelta(minutes=config.MINUTOS_BLOQUEIO + 1)
    rotas_auth.tentativas.clear()
    for i in range(rotas_auth.MAX_REGISTROS + 5):
        rotas_auth.tentativas[("1.1.1.1", f"x{i}@univille.br")] = {"erros": 1, "bloqueado_ate": None, "ultima": antigo}
    cliente.post("/auth/login", json={"email": "limpeza@univille.br", "senha": "qualquer123"})
    assert len(rotas_auth.tentativas) < 10


def test_email_gigante_no_login_nao_e_guardado(cliente):
    r = cliente.post("/auth/login", json={"email": "a" * 5000 + "@univille.br", "senha": "x"})
    assert r.status_code == 401
    assert not any(len(e) > 150 for _, e in rotas_auth.tentativas)


# VULN-05 ------------------------------------------------------------------
def test_login_gasta_tempo_parecido_com_email_inexistente(cliente, passageiro):
    def medir(email):
        ini = time.perf_counter()
        for _ in range(3):
            cliente.post("/auth/login", json={"email": email, "senha": "errada1234"})
            rotas_auth.tentativas.clear()
        return (time.perf_counter() - ini) / 3
    existe, nao_existe = medir(passageiro.email), medir(f"nao.{uuid.uuid4().hex[:6]}@univille.br")
    assert nao_existe > existe * 0.5  # antes da correção era ~6x mais rápido


# VULN-06 ------------------------------------------------------------------
def test_senha_com_mais_de_72_bytes(cliente):
    r = cliente.post("/auth/cadastro", json=_dados(senha="a" * 100))
    assert r.status_code == 422 and "72" in r.json()["detail"]
    r = cliente.post("/auth/login", json={"email": "teste.x@univille.br", "senha": "a" * 100})
    assert r.status_code == 401


# VULN-07 ------------------------------------------------------------------
def test_docs_desligados_fora_do_modo_demo():
    codigo = "from app.main import app; print(app.docs_url, app.openapi_url)"
    e = dict(os.environ, MODO_DEMO="false", SECRET_KEY="x" * 40)
    r = subprocess.run([sys.executable, "-c", codigo], env=e, capture_output=True, text=True)
    assert r.stdout.strip() == "None None", r.stderr


# VULN-08 e VULN-09 ---------------------------------------------------------
def test_cabecalhos_de_seguranca(cliente):
    h = cliente.get("/").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "no-referrer"
    assert h["cache-control"] == "no-store"


def test_cors_so_metodos_usados(cliente):
    r = cliente.options("/perfil", headers={"Origin": "http://localhost:5173",
                                            "Access-Control-Request-Method": "PATCH"})
    assert r.status_code == 400  # PATCH não é permitido
    r = cliente.options("/perfil", headers={"Origin": "http://evil.example",
                                            "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers


# VULN-11 ------------------------------------------------------------------
def test_solicitacao_duplicada_simultanea_da_409(cliente, motorista, passageiro, criar_carona):
    from concurrent.futures import ThreadPoolExecutor
    carona = criar_carona(motorista)
    with ThreadPoolExecutor(2) as ex:
        codigos = list(ex.map(lambda _: passageiro.post(f"/caronas/{carona}/solicitacoes").status_code, range(2)))
    assert sorted(codigos) == [201, 409]


# Confirmados como NÃO vulneráveis (regressão) -----------------------------
def test_sql_injection_no_login_e_na_busca(cliente, passageiro):
    r = cliente.post("/auth/login", json={"email": "' OR '1'='1", "senha": "' OR '1'='1"})
    assert r.status_code == 401
    r = passageiro.get("/caronas", params={"data": "2030-01-01' OR 1=1 --"})
    assert r.status_code in (400, 422)
    assert sql("SELECT count(*) FROM usuario")[0][0] > 0


def test_nao_acessa_veiculo_de_outro_usuario(cliente, motorista, passageiro):
    vid = motorista.get("/veiculos").json()[0]["id"]
    assert passageiro.put(f"/veiculos/{vid}", json={"modelo": "X1", "cor": "Azul", "placa": "ZZZ9Z99", "vagas": 2}).status_code in (403, 404)
    assert passageiro.delete(f"/veiculos/{vid}").status_code in (403, 404)


def test_telefone_e_placa_ocultos_antes_do_aceite(cliente, motorista, passageiro, criar_carona):
    carona = criar_carona(motorista)
    passageiro.post(f"/caronas/{carona}/solicitacoes")
    d = passageiro.get(f"/caronas/{carona}").json()
    assert not d.get("telefone_motorista") and not d.get("veiculo_placa")


# VULN-13 ------------------------------------------------------------------
def test_tentativas_simultaneas_nao_passam_do_limite(cliente, passageiro, monkeypatch):
    """10 chutes ao mesmo tempo: no máximo 5 chegam a conferir a senha."""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    conferidas, trava, barreira = [], threading.Lock(), threading.Barrier(5, timeout=3)

    def falsa(senha, hash_):
        with trava:
            conferidas.append(1)
        try:
            barreira.wait()  # segura as primeiras 5 juntas, como num ataque simultâneo
        except threading.BrokenBarrierError:
            pass
        return False

    monkeypatch.setattr(rotas_auth, "senha_confere", falsa)
    rotas_auth.tentativas.clear()
    corpo = {"email": passageiro.email, "senha": "errada1234"}
    with ThreadPoolExecutor(10) as ex:
        codigos = list(ex.map(lambda _: cliente.post("/auth/login", json=corpo).status_code, range(10)))
    assert len(conferidas) <= config.MAX_TENTATIVAS
    assert codigos.count(429) >= 5
