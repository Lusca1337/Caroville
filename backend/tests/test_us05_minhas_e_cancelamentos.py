"""US05 - Minhas caronas e cancelamentos (RF12, RF13, RF14; RN08, RN09)."""
from datetime import timedelta

from tests.conftest import agora, sql


def test_minhas_oferecidas_com_contagem_de_pendentes(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    passageiro.post(f"/caronas/{cid}/solicitacoes")
    r = motorista.get("/minhas/oferecidas")
    assert r.status_code == 200
    minha = [c for c in r.json() if c["id"] == cid][0]
    assert minha["pendentes"] == 1 and minha["status"] == "ABERTA"
    assert passageiro.get("/minhas/oferecidas").json() == []


def test_minhas_solicitadas_com_status_do_pedido(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    item = passageiro.get("/minhas/solicitadas").json()[0]
    assert item["carona_id"] == cid and item["solicitacao_status"] == "PENDENTE"
    assert item["telefone_motorista"] is None
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    item = passageiro.get("/minhas/solicitadas").json()[0]
    assert item["solicitacao_status"] == "CONFIRMADA" and item["telefone_motorista"] == "(47) 99999-0000"


def test_passageiro_cancela_solicitacao_e_a_vaga_volta(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista, vagas=1)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    assert motorista.get(f"/caronas/{cid}").json()["status"] == "LOTADA"
    r = passageiro.post(f"/solicitacoes/{sid}/cancelar")
    assert r.status_code == 200 and r.json()["mensagem"] == "Solicitação cancelada"
    d = motorista.get(f"/caronas/{cid}").json()
    assert d["vagas_disponiveis"] == 1 and d["status"] == "ABERTA"


def test_cancelar_solicitacao_pendente_nao_mexe_nas_vagas(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista, vagas=2)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert passageiro.post(f"/solicitacoes/{sid}/cancelar").status_code == 200
    assert motorista.get(f"/caronas/{cid}").json()["vagas_disponiveis"] == 2


def test_cancelamento_de_solicitacao_com_erros(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert passageiro2.post(f"/solicitacoes/{sid}/cancelar").status_code == 403
    assert passageiro.post("/solicitacoes/99999999/cancelar").status_code == 404
    passageiro.post(f"/solicitacoes/{sid}/cancelar")
    assert passageiro.post(f"/solicitacoes/{sid}/cancelar").status_code == 409


def test_prazo_de_2h_para_cancelar_solicitacao_rn08(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista, agora() + timedelta(minutes=90))
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    r = passageiro.post(f"/solicitacoes/{sid}/cancelar")
    assert r.status_code == 409 and r.json()["detail"] == "Prazo de cancelamento encerrado"


def test_prazo_de_2h_para_cancelar_carona_rn08(motorista, criar_carona):
    cid = criar_carona(motorista, agora() + timedelta(minutes=90))
    r = motorista.post(f"/caronas/{cid}/cancelar")
    assert r.status_code == 409 and r.json()["detail"] == "Prazo de cancelamento encerrado"


def test_motorista_cancela_carona_e_cancela_as_solicitacoes_rn09(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista, vagas=3)
    s1 = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    s2 = passageiro2.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{s1}/aceitar")
    r = motorista.post(f"/caronas/{cid}/cancelar")
    assert r.status_code == 200 and r.json()["mensagem"] == "Carona cancelada"
    assert motorista.get(f"/caronas/{cid}").json()["status"] == "CANCELADA"
    assert {x["status"] for x in motorista.get(f"/caronas/{cid}/solicitacoes").json()} == {"CANCELADA"}
    assert sql("SELECT count(*) FROM solicitacao WHERE carona_id = %s AND status = 'CANCELADA'", (cid,))[0][0] == 2


def test_so_o_motorista_cancela_a_carona_e_so_uma_vez(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    assert passageiro.post(f"/caronas/{cid}/cancelar").status_code == 403
    assert motorista.post("/caronas/99999999/cancelar").status_code == 404
    assert motorista.post(f"/caronas/{cid}/cancelar").status_code == 200
    assert motorista.post(f"/caronas/{cid}/cancelar").status_code == 409
