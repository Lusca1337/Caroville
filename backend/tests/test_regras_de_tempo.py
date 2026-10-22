"""RN11 e RN13: o que acontece quando o horário da carona passa.

Para simular a passagem do tempo, o teste muda a data de saída direto no banco.
"""
from datetime import timedelta

from tests.conftest import agora, sql


def passar_o_horario(carona_id):
    sql("UPDATE carona SET saida_em = %s WHERE id = %s", (agora() - timedelta(hours=1), carona_id))


def test_carona_que_ja_saiu_vira_concluida_rn13(motorista, criar_carona):
    cid = criar_carona(motorista)
    passar_o_horario(cid)
    status = {c["id"]: c["status"] for c in motorista.get("/minhas/oferecidas").json()}
    assert status[cid] == "CONCLUIDA"


def test_carona_cancelada_continua_cancelada_rn13(motorista, criar_carona):
    cid = criar_carona(motorista)
    motorista.post(f"/caronas/{cid}/cancelar")
    passar_o_horario(cid)
    status = {c["id"]: c["status"] for c in motorista.get("/minhas/oferecidas").json()}
    assert status[cid] == "CANCELADA"


def test_solicitacao_pendente_expira_quando_a_carona_sai_rn11(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    passar_o_horario(cid)
    passageiro.get("/minhas/solicitadas")  # qualquer consulta dispara a atualização
    assert sql("SELECT status FROM solicitacao WHERE id = %s", (sid,))[0][0] == "EXPIRADA"


def test_solicitacao_confirmada_nao_expira(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    sid = passageiro.post(f"/caronas/{cid}/solicitacoes").json()["id"]
    motorista.post(f"/solicitacoes/{sid}/aceitar")
    passar_o_horario(cid)
    passageiro.get("/minhas/solicitadas")
    assert sql("SELECT status FROM solicitacao WHERE id = %s", (sid,))[0][0] == "CONFIRMADA"


def test_nao_solicita_carona_que_ja_saiu(motorista, passageiro, criar_carona):
    cid = criar_carona(motorista)
    passar_o_horario(cid)
    r = passageiro.post(f"/caronas/{cid}/solicitacoes")
    assert r.status_code == 409
