"""US06 - Perfil e veículo (RF04, RF05, RN02)."""
from tests.conftest import placa


def test_ver_perfil(passageiro):
    r = passageiro.get("/perfil")
    assert r.status_code == 200
    assert r.json()["email"] == passageiro.email
    assert "senha_hash" not in r.json()


def test_editar_perfil(passageiro):
    r = passageiro.put("/perfil", json={"nome": "Novo Nome", "curso": "Engenharia", "telefone": "(47) 91111-2222"})
    assert r.status_code == 200
    p = passageiro.get("/perfil").json()
    assert (p["nome"], p["curso"], p["telefone"]) == ("Novo Nome", "Engenharia", "(47) 91111-2222")


def test_editar_perfil_com_dados_invalidos(passageiro):
    r = passageiro.put("/perfil", json={"nome": "A", "curso": "Engenharia", "telefone": "(47) 91111-2222"})
    assert r.status_code == 422
    r = passageiro.put("/perfil", json={"nome": "Ana", "curso": "Engenharia", "telefone": "12"})
    assert r.status_code == 422


def test_cadastrar_listar_editar_e_excluir_veiculo(passageiro):
    p1, p2 = placa(), placa()
    r = passageiro.post("/veiculos", json={"modelo": "Gol", "cor": "Branco", "placa": p1, "lugares": 5})
    assert r.status_code == 201
    vid = r.json()["id"]
    assert [(v["modelo"], v["placa"]) for v in passageiro.get("/veiculos").json()] == [("Gol", p1)]
    r = passageiro.put(f"/veiculos/{vid}", json={"modelo": "Gol G6", "cor": "Preto", "placa": p2, "lugares": 4})
    assert r.status_code == 200 and (r.json()["modelo"], r.json()["placa"]) == ("Gol G6", p2)
    assert passageiro.delete(f"/veiculos/{vid}").status_code == 200
    assert passageiro.get("/veiculos").json() == []


def test_validacao_do_veiculo(passageiro):
    for corpo in ({"modelo": "Gol", "cor": "Branco", "placa": placa(), "lugares": 1},
                  {"modelo": "Gol", "cor": "Branco", "placa": placa(), "lugares": 9},
                  {"modelo": "", "cor": "Branco", "placa": placa(), "lugares": 4},
                  {"modelo": "Gol", "cor": "", "placa": placa(), "lugares": 4},
                  {"modelo": "Gol", "cor": "Branco", "placa": placa(), "lugares": "muitos"},
                  {"modelo": "Gol", "cor": "Branco", "lugares": 4}):
        assert passageiro.post("/veiculos", json=corpo).status_code == 422, corpo


def test_placa_aceita_padrao_antigo_e_mercosul_e_grava_sem_hifen(novo_usuario):
    sufixo = placa()[1:3]  # letras aleatórias para não repetir placa entre execuções
    for digitada, gravada in ((f"z{sufixo.lower()}-1234", f"Z{sufixo}1234"), (f"Z{sufixo} 1D23", f"Z{sufixo}1D23")):
        r = novo_usuario().post("/veiculos", json={"modelo": "Gol", "cor": "Branco", "placa": digitada, "lugares": 4})
        assert r.status_code == 201 and r.json()["placa"] == gravada, r.text


def test_placa_invalida(passageiro):
    for invalida in ("AB123", "ABCD123", "1234ABC", "ABC12345", ""):
        r = passageiro.post("/veiculos", json={"modelo": "Gol", "cor": "Branco", "placa": invalida, "lugares": 4})
        assert r.status_code == 422 and r.json()["detail"] == "Placa inválida. Use ABC-1234 ou ABC1D23", invalida


def test_placa_repetida(motorista, passageiro):
    ja_usada = motorista.get("/veiculos").json()[0]["placa"]
    r = passageiro.post("/veiculos", json={"modelo": "Gol", "cor": "Branco", "placa": ja_usada, "lugares": 4})
    assert r.status_code == 409 and r.json()["detail"] == "Esta placa já está cadastrada"


def test_nao_mexe_no_veiculo_de_outra_pessoa(motorista, passageiro):
    vid = motorista.get("/veiculos").json()[0]["id"]
    corpo = {"modelo": "Hack", "cor": "Preto", "placa": placa(), "lugares": 4}
    assert passageiro.put(f"/veiculos/{vid}", json=corpo).status_code == 404
    assert passageiro.delete(f"/veiculos/{vid}").status_code == 404
    assert motorista.get("/veiculos").json()[0]["modelo"] == "Fiat Argo"


def test_veiculo_usado_em_carona_nao_pode_ser_excluido(motorista, criar_carona):
    criar_carona(motorista)
    vid = motorista.get("/veiculos").json()[0]["id"]
    r = motorista.delete(f"/veiculos/{vid}")
    assert r.status_code == 409 and "não pode ser excluído" in r.json()["detail"]


def test_lista_de_locais_tem_campus_e_bairros(cliente):
    r = cliente.get("/locais")
    assert r.status_code == 200
    tipos = [l["tipo"] for l in r.json()]
    assert tipos.count("CAMPUS") == 1 and tipos.count("BAIRRO") >= 2
