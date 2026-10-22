"""Integração entre frontend, backend e banco.

O frontend (React, porta 5173) conversa com a API pelo navegador, então o backend
precisa liberar essa origem (CORS) e devolver erros no formato {"detail": "..."},
que é o que as telas exibem. O roteiro completo pelas telas está em docs/testes.md.
"""


def test_cors_libera_o_frontend(cliente):
    r = cliente.options("/auth/login", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_nao_libera_outras_origens(cliente):
    r = cliente.options("/auth/login", headers={
        "Origin": "http://site-qualquer.com", "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in r.headers


def test_erros_voltam_no_formato_que_o_frontend_exibe(cliente, passageiro):
    for r in (cliente.post("/auth/login", json={"email": "teste.a@univille.br", "senha": "x"}),
              cliente.post("/auth/cadastro", json={}),
              passageiro.get("/caronas/99999999"),
              cliente.get("/perfil")):
        assert isinstance(r.json()["detail"], str)


def test_fluxo_completo_cadastro_ate_carona_confirmada(cliente, novo_usuario, campus, bairro):
    """Os mesmos passos que as telas fazem: cadastro, login, veículo, oferecer, buscar, solicitar, aceitar."""
    from datetime import timedelta
    from tests.conftest import agora, iso, placa, sql

    mot, pas = novo_usuario(), novo_usuario()
    mot.post("/veiculos", json={"modelo": "Onix", "cor": "Azul", "placa": placa(), "lugares": 4})
    saida = agora() + timedelta(days=3)
    cid = mot.post("/caronas", json={"origem_id": bairro, "destino_id": campus,
                                     "saida_em": iso(saida), "vagas_total": 2}).json()["id"]
    achadas = pas.get("/caronas", params={"origem_id": bairro, "destino_id": campus, "horario": iso(saida)}).json()
    assert cid in [c["id"] for c in achadas]
    sid = pas.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert mot.post(f"/solicitacoes/{sid}/aceitar").status_code == 200
    assert pas.get("/minhas/solicitadas").json()[0]["solicitacao_status"] == "CONFIRMADA"
    assert sql("SELECT vagas_disponiveis FROM carona WHERE id = %s", (cid,))[0][0] == 1
