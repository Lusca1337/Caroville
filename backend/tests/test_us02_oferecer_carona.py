"""US02 - Oferecer carona (RF06; RN02, RN03, RN04, RN14)."""
from datetime import timedelta

from tests.conftest import agora, iso


def corpo(campus, bairro, quando=None, vagas=3, **extra):
    c = {"origem_id": bairro, "destino_id": campus,
         "saida_em": iso(quando or agora() + timedelta(days=1)), "vagas_total": vagas}
    c.update(extra)
    return c


def test_publicar_carona_valida(motorista, campus, bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro, ponto_encontro="Praça", observacoes="Sem fumar"))
    assert r.status_code == 201
    d = motorista.get(f"/caronas/{r.json()['id']}").json()
    assert d["status"] == "ABERTA" and d["vagas_disponiveis"] == 3 and d["vagas_total"] == 3
    assert d["origem"] == "Costa e Silva" and d["destino"] == "Campus Univille"


def test_carona_de_volta_do_campus_para_o_bairro(motorista, campus, bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro) | {"origem_id": campus, "destino_id": bairro})
    assert r.status_code == 201


def test_sem_veiculo_nao_oferece_carona_rn02(passageiro, campus, bairro):
    r = passageiro.post("/caronas", json=corpo(campus, bairro))
    assert r.status_code == 409 and "veículo" in r.json()["detail"]


def test_vagas_de_1_a_4_rn03(motorista, campus, bairro):
    for vagas in (0, 5, -1):
        r = motorista.post("/caronas", json=corpo(campus, bairro, vagas=vagas))
        assert r.status_code == 422 and "1 a 4" in r.json()["detail"], vagas
    for vagas in (1, 4):
        assert motorista.post("/caronas", json=corpo(campus, bairro, vagas=vagas)).status_code == 201


def test_antecedencia_minima_de_1_hora_rn04(motorista, campus, bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro, quando=agora() + timedelta(minutes=30)))
    assert r.status_code == 422 and r.json()["detail"] == "Informe um horário futuro"
    r = motorista.post("/caronas", json=corpo(campus, bairro, quando=agora() - timedelta(days=1)))
    assert r.status_code == 422
    r = motorista.post("/caronas", json=corpo(campus, bairro, quando=agora() + timedelta(hours=1, minutes=5)))
    assert r.status_code == 201


def test_campus_obrigatorio_na_saida_ou_destino_rn14(motorista, campus, bairro, outro_bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro) | {"origem_id": bairro, "destino_id": outro_bairro})
    assert r.status_code == 422 and "Campus Univille" in r.json()["detail"]


def test_saida_e_destino_diferentes(motorista, campus, bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro) | {"origem_id": campus, "destino_id": campus})
    assert r.status_code == 422 and r.json()["detail"] == "Saída e destino devem ser diferentes"


def test_local_inexistente(motorista, campus, bairro):
    r = motorista.post("/caronas", json=corpo(campus, bairro) | {"origem_id": 999999})
    assert r.status_code == 422


def test_veiculo_de_outra_pessoa_e_recusado(motorista, novo_usuario, campus, bairro):
    outro = novo_usuario(com_veiculo=True)
    vid = outro.get("/veiculos").json()[0]["id"]
    r = motorista.post("/caronas", json=corpo(campus, bairro, veiculo_id=vid))
    assert r.status_code == 404


def test_campos_invalidos_ou_faltando(motorista, campus, bairro):
    assert motorista.post("/caronas", json={"origem_id": bairro}).json()["detail"] == "Preencha todos os campos"
    r = motorista.post("/caronas", json=corpo(campus, bairro) | {"saida_em": "lixo"})
    assert r.status_code == 422 and "inválido" in r.json()["detail"]
    r = motorista.post("/caronas", json=corpo(campus, bairro, ponto_encontro="x" * 121))
    assert r.status_code == 422
    r = motorista.post("/caronas", json=corpo(campus, bairro, observacoes="x" * 256))
    assert r.status_code == 422
