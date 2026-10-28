"""US03 - Buscar carona e solicitar vaga (RF07, RF08, RF09; RN05, RN06, RN10)."""
from datetime import timedelta

from tests.conftest import agora


def buscar(usuario, origem, destino, quando):
    """Busca pelo dia (só a data de 'quando' importa)."""
    return usuario.get("/caronas", params={"origem_id": origem, "destino_id": destino, "data": quando.date().isoformat()})


def test_busca_acha_as_caronas_do_dia_escolhido(motorista, passageiro, criar_carona, campus, bairro):
    dia = (agora() + timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0)
    cedo, tarde = criar_carona(motorista, dia + timedelta(hours=7)), criar_carona(motorista, dia + timedelta(hours=22))
    for quando, deve_achar in ((dia, True), (dia - timedelta(days=1), False), (dia + timedelta(days=1), False)):
        r = buscar(passageiro, bairro, campus, quando)
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert (cedo in ids and tarde in ids) is deve_achar, quando
    ids = [c["id"] for c in buscar(passageiro, bairro, campus, dia).json()]
    assert ids.index(cedo) < ids.index(tarde)  # da mais cedo para a mais tarde


def test_busca_com_data_invalida(passageiro, campus, bairro):
    r = passageiro.get("/caronas", params={"origem_id": bairro, "destino_id": campus, "data": "lixo"})
    assert r.status_code == 422 and r.json()["detail"] == "Data ou horário inválido"


def test_busca_filtra_por_saida_e_destino(motorista, passageiro, criar_carona, campus, bairro, outro_bairro):
    saida = agora() + timedelta(days=1, hours=4)
    cid = criar_carona(motorista, saida)
    assert cid not in [c["id"] for c in buscar(passageiro, outro_bairro, campus, saida).json()]
    assert cid not in [c["id"] for c in buscar(passageiro, campus, bairro, saida).json()]


def test_busca_nao_mostra_as_proprias_caronas(motorista, criar_carona, campus, bairro):
    saida = agora() + timedelta(days=1, hours=5)
    cid = criar_carona(motorista, saida)
    assert cid not in [c["id"] for c in buscar(motorista, bairro, campus, saida).json()]


def test_busca_exige_todos_os_filtros(passageiro, bairro):
    assert passageiro.get("/caronas", params={"origem_id": bairro}).status_code == 422


def test_busca_nao_mostra_caronas_lotadas_nem_canceladas(motorista, passageiro, passageiro2, criar_carona, campus, bairro):
    saida = agora() + timedelta(days=1, hours=6)
    lotada = criar_carona(motorista, saida, vagas=1)
    sid = passageiro.post(f"/caronas/{lotada}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    cancelada = criar_carona(motorista, saida + timedelta(hours=3))
    motorista.post(f"/caronas/{cancelada}/cancelar")
    achadas = [c["id"] for c in buscar(passageiro2, bairro, campus, saida).json()]
    assert lotada not in achadas
    assert cancelada not in [c["id"] for c in buscar(passageiro2, bairro, campus, saida + timedelta(hours=3)).json()]


def test_detalhe_da_carona(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    d = passageiro.get(f"/caronas/{cid}").json()
    assert d["veiculo_modelo"] == "Fiat Argo" and d["ponto_encontro"] == "Praça central"
    assert d["sou_motorista"] is False and d["telefone_motorista"] is None
    assert motorista.get(f"/caronas/{cid}").json()["sou_motorista"] is True


def test_detalhe_de_carona_inexistente(passageiro):
    assert passageiro.get("/caronas/99999999").status_code == 404


def test_solicitar_vaga(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    r = passageiro.post(f"/caronas/{cid}/solicitacoes")
    assert r.status_code == 201
    d = passageiro.get(f"/caronas/{cid}").json()
    assert d["minha_solicitacao_status"] == "PENDENTE"
    assert d["vagas_disponiveis"] == 3  # só diminui quando o motorista aceita


def test_motorista_nao_solicita_a_propria_carona_rn05(motorista, criar_carona):
    cid = criar_carona(motorista)
    r = motorista.post(f"/caronas/{cid}/solicitacoes")
    assert r.status_code == 409 and "própria carona" in r.json()["detail"]


def test_nao_pode_ter_duas_solicitacoes_ativas_rn06(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    passageiro.post(f"/caronas/{cid}/solicitacoes")
    r = passageiro.post(f"/caronas/{cid}/solicitacoes")
    assert r.status_code == 409 and "solicitação ativa" in r.json()["detail"]


def test_solicitar_carona_inexistente(passageiro):
    assert passageiro.post("/caronas/99999999/solicitacoes").status_code == 404


def test_solicitar_carona_lotada_ou_cancelada(motorista, passageiro, passageiro2, novo_usuario, criar_carona):
    lotada = criar_carona(motorista, vagas=1)
    sid = passageiro.post(f"/caronas/{lotada}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    r = passageiro2.post(f"/caronas/{lotada}/solicitacoes")
    assert r.status_code == 409 and r.json()["detail"] == "Carona lotada"

    cancelada = criar_carona(motorista)
    motorista.post(f"/caronas/{cancelada}/cancelar")
    r = passageiro2.post(f"/caronas/{cancelada}/solicitacoes")
    assert r.status_code == 409 and "não está mais disponível" in r.json()["detail"]


def test_telefone_do_motorista_so_aparece_depois_do_aceite_rn10(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    assert passageiro.get(f"/caronas/{cid}").json()["telefone_motorista"] is None
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    assert passageiro.get(f"/caronas/{cid}").json()["telefone_motorista"] == "(47) 99999-0000"
