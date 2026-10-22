"""US04 - Aceitar ou recusar solicitações (RF10, RF11; RN07, RN10, RN12)."""
from datetime import timedelta

from tests.conftest import agora, sql


def test_motorista_ve_as_solicitacoes_sem_telefone_dos_pendentes(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista)
    passageiro.post(f"/caronas/{cid}/solicitacoes")
    s2 = passageiro2.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{s2}/aceitar")
    lista = motorista.get(f"/caronas/{cid}/solicitacoes").json()
    assert len(lista) == 2
    por_status = {x["status"]: x["telefone"] for x in lista}
    assert por_status["PENDENTE"] is None  # RN10
    assert por_status["CONFIRMADA"] == "(47) 99999-0000"


def test_placa_do_carro_so_aparece_depois_do_aceite_rn10(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista)
    placa = motorista.get("/veiculos").json()[0]["placa"]
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert passageiro.get(f"/caronas/{cid}").json()["veiculo_placa"] is None
    assert passageiro.get("/minhas/solicitadas").json()[0]["veiculo_placa"] is None
    assert passageiro2.get(f"/caronas/{cid}").json()["veiculo_placa"] is None  # quem nem pediu também não vê
    assert motorista.get(f"/caronas/{cid}").json()["veiculo_placa"] == placa  # o motorista vê a própria placa

    motorista.post(f"/solicitacoes/{sid}/aceitar")
    assert passageiro.get(f"/caronas/{cid}").json()["veiculo_placa"] == placa
    assert passageiro.get("/minhas/solicitadas").json()[0]["veiculo_placa"] == placa


def test_so_o_motorista_ve_e_responde_solicitacoes(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert passageiro2.get(f"/caronas/{cid}/solicitacoes").status_code == 403
    assert passageiro.post(f"/solicitacoes/{sid}/aceitar").status_code == 403
    assert passageiro.post(f"/solicitacoes/{sid}/recusar").status_code == 403
    assert motorista.get("/caronas/99999999/solicitacoes").status_code == 404
    assert motorista.post("/solicitacoes/99999999/aceitar").status_code == 404


def test_aceitar_desconta_uma_vaga_rn07(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista, vagas=3)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    r = motorista.post(f"/solicitacoes/{sid}/aceitar")
    assert r.status_code == 200 and r.json()["mensagem"] == "Solicitação aceita"
    assert motorista.get(f"/caronas/{cid}").json()["vagas_disponiveis"] == 2


def test_ultima_vaga_deixa_a_carona_lotada(motorista, passageiro, passageiro2, criar_carona):
    cid = criar_carona(motorista, vagas=1)
    s1 = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    s2 = passageiro2.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert motorista.post(f"/solicitacoes/{s1}/aceitar").status_code == 200
    assert motorista.get(f"/caronas/{cid}").json()["status"] == "LOTADA"
    r = motorista.post(f"/solicitacoes/{s2}/aceitar")
    assert r.status_code == 409 and r.json()["detail"] == "Carona lotada"


def test_recusar_nao_desconta_vaga(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista, vagas=2)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    r = motorista.post(f"/solicitacoes/{sid}/recusar")
    assert r.status_code == 200 and r.json()["mensagem"] == "Solicitação recusada"
    assert motorista.get(f"/caronas/{cid}").json()["vagas_disponiveis"] == 2


def test_nao_responde_duas_vezes_a_mesma_solicitacao(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    for acao in ("aceitar", "recusar"):
        r = motorista.post(f"/solicitacoes/{sid}/{acao}")
        assert r.status_code == 409 and "já foi respondida" in r.json()["detail"]


def test_pode_pedir_de_novo_depois_de_recusado(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/recusar")
    assert passageiro.post(f"/caronas/{cid}/solicitacoes").status_code == 201


def test_passageiro_nao_confirma_duas_caronas_com_menos_de_1h_de_diferenca_rn12(motorista, passageiro, criar_carona):
    saida = agora() + timedelta(days=2)
    c1 = criar_carona(motorista, saida)
    c2 = criar_carona(motorista, saida + timedelta(minutes=30))
    s1 = passageiro.post(f"/caronas/{c1}/solicitacoes").json()["id"]
    s2 = passageiro.post(f"/caronas/{c2}/solicitacoes").json()["id"]
    assert motorista.post(f"/solicitacoes/{s1}/aceitar").status_code == 200
    r = motorista.post(f"/solicitacoes/{s2}/aceitar")
    assert r.status_code == 409 and "horário muito próximo" in r.json()["detail"]


def test_caronas_com_1h_ou_mais_de_diferenca_podem_ser_confirmadas(motorista, passageiro, criar_carona):
    saida = agora() + timedelta(days=2)
    c1 = criar_carona(motorista, saida)
    c2 = criar_carona(motorista, saida + timedelta(hours=2))
    s1 = passageiro.post(f"/caronas/{c1}/solicitacoes").json()["id"]
    s2 = passageiro.post(f"/caronas/{c2}/solicitacoes").json()["id"]
    assert motorista.post(f"/solicitacoes/{s1}/aceitar").status_code == 200
    assert motorista.post(f"/solicitacoes/{s2}/aceitar").status_code == 200


def test_dados_ficam_gravados_no_banco(motorista, passageiro, criar_carona):
    """Integração API -> banco: o que a API responde bate com o que está salvo."""
    cid = criar_carona(motorista, vagas=2)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    assert sql("SELECT status, respondido_em IS NOT NULL FROM solicitacao WHERE id = %s", (sid,))[0] == ("CONFIRMADA", True)
    assert sql("SELECT vagas_disponiveis, status FROM carona WHERE id = %s", (cid,))[0] == (1, "ABERTA")
