"""US02 a US05 - Caronas e solicitações (RF06 a RF16)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.avisos import avisar
from app.db import get_db
from app.modelos import CaronaNova
from app.seguranca import usuario_logado

router = APIRouter(tags=["Caronas e solicitações"])

HORAS_MIN_ANTECEDENCIA = 1    # RN04
HORAS_PRAZO_CANCELAMENTO = 2  # RN08
JANELA_BUSCA_MINUTOS = 30     # RF07

# Consulta base: carona com nomes do motorista, do veículo e dos locais
BASE_SELECT = """
    SELECT c.id, c.saida_em, c.vagas_total, c.vagas_disponiveis, c.ponto_encontro,
           c.observacoes, c.status, c.motorista_id, c.origem_id, c.destino_id,
           u.nome AS motorista_nome, v.modelo AS veiculo_modelo, v.cor AS veiculo_cor,
           o.nome AS origem, d.nome AS destino
    FROM carona c
    JOIN usuario u ON u.id = c.motorista_id
    JOIN veiculo v ON v.id = c.veiculo_id
    JOIN local o ON o.id = c.origem_id
    JOIN local d ON d.id = c.destino_id
"""


def atualizar_status_automaticos(db):
    """RN11 e RN13: atualiza o que já passou do horário."""
    agora = datetime.now()
    # RN11: solicitações pendentes de caronas que já saíram viram "Expirada"
    db.execute(
        """UPDATE solicitacao SET status = 'EXPIRADA', respondido_em = %s
           WHERE status = 'PENDENTE'
             AND carona_id IN (SELECT id FROM carona WHERE saida_em < %s)""",
        (agora, agora),
    )
    # RN13: caronas que já saíram e não foram canceladas viram "Concluída"
    db.execute(
        """UPDATE carona SET status = 'CONCLUIDA'
           WHERE status IN ('ABERTA', 'LOTADA') AND saida_em < %s""",
        (agora,),
    )


def db_atualizado(db=Depends(get_db)):
    atualizar_status_automaticos(db)
    return db


def prazo_de_cancelamento_encerrado(saida_em: datetime) -> bool:
    """RN08: só dá para cancelar até 2 horas antes da saída."""
    return saida_em - datetime.now() < timedelta(hours=HORAS_PRAZO_CANCELAMENTO)


# ---------------------------------------------------------------- US02

@router.post("/caronas", status_code=201)
def oferecer_carona(
    dados: CaronaNova, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    veiculos = db.execute(
        "SELECT id FROM veiculo WHERE usuario_id = %s ORDER BY id", (usuario["id"],)
    ).fetchall()
    if not veiculos:  # RN02
        raise HTTPException(409, "Cadastre um veículo no seu perfil antes de oferecer carona")
    ids = [v["id"] for v in veiculos]
    veiculo_id = dados.veiculo_id or ids[0]
    if veiculo_id not in ids:
        raise HTTPException(404, "Veículo não encontrado")

    if dados.saida_em < datetime.now() + timedelta(hours=HORAS_MIN_ANTECEDENCIA):  # RN04
        raise HTTPException(422, "Informe um horário futuro")

    n = db.execute(
        "SELECT count(*) AS n FROM local WHERE id IN (%s, %s)",
        (dados.origem_id, dados.destino_id),
    ).fetchone()["n"]
    if n != 2:
        raise HTTPException(422, "Local de saída ou de destino inválido")

    carona = db.execute(
        """INSERT INTO carona (motorista_id, veiculo_id, origem_id, destino_id, saida_em,
                               vagas_total, vagas_disponiveis, ponto_encontro, observacoes)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (usuario["id"], veiculo_id, dados.origem_id, dados.destino_id, dados.saida_em,
         dados.vagas_total, dados.vagas_total, dados.ponto_encontro, dados.observacoes),
    ).fetchone()
    return {"mensagem": "Carona publicada com sucesso", "id": carona["id"]}


# ---------------------------------------------------------------- US03

@router.get("/caronas")
def buscar_caronas(
    origem_id: int,
    destino_id: int,
    horario: datetime,
    usuario=Depends(usuario_logado),
    db=Depends(db_atualizado),
):
    """RF07: caronas abertas com saída até 30 minutos antes ou depois do horário."""
    if horario.tzinfo is not None:
        horario = horario.astimezone().replace(tzinfo=None)
    janela = timedelta(minutes=JANELA_BUSCA_MINUTOS)
    return db.execute(
        BASE_SELECT
        + """ WHERE c.status = 'ABERTA' AND c.origem_id = %s AND c.destino_id = %s
                AND c.saida_em BETWEEN %s AND %s
              ORDER BY c.saida_em""",
        (origem_id, destino_id, horario - janela, horario + janela),
    ).fetchall()


@router.get("/caronas/{carona_id}")
def ver_carona(carona_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)):
    """RF08: detalhes da carona."""
    carona = db.execute(BASE_SELECT + " WHERE c.id = %s", (carona_id,)).fetchone()
    if carona is None:
        raise HTTPException(404, "Carona não encontrada")

    minha = db.execute(
        """SELECT id, status FROM solicitacao
           WHERE carona_id = %s AND passageiro_id = %s
           ORDER BY (status IN ('PENDENTE', 'CONFIRMADA')) DESC, id DESC LIMIT 1""",
        (carona_id, usuario["id"]),
    ).fetchone()
    carona["sou_motorista"] = carona["motorista_id"] == usuario["id"]
    carona["minha_solicitacao_id"] = minha["id"] if minha else None
    carona["minha_solicitacao_status"] = minha["status"] if minha else None

    # RN10: o telefone do motorista só aparece depois do aceite
    carona["telefone_motorista"] = None
    if minha and minha["status"] == "CONFIRMADA":
        carona["telefone_motorista"] = db.execute(
            "SELECT telefone FROM usuario WHERE id = %s", (carona["motorista_id"],)
        ).fetchone()["telefone"]
    return carona


@router.post("/caronas/{carona_id}/solicitacoes", status_code=201)
def solicitar_carona(
    carona_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    """RF09: o passageiro pede uma vaga."""
    carona = db.execute(BASE_SELECT + " WHERE c.id = %s", (carona_id,)).fetchone()
    if carona is None:
        raise HTTPException(404, "Carona não encontrada")
    if carona["motorista_id"] == usuario["id"]:  # RN05
        raise HTTPException(409, "Você não pode solicitar vaga na sua própria carona")
    if carona["status"] == "LOTADA":
        raise HTTPException(409, "Carona lotada")
    if carona["status"] != "ABERTA":
        raise HTTPException(409, "Esta carona não está mais disponível")

    ja_tem = db.execute(  # RN06
        """SELECT 1 FROM solicitacao
           WHERE carona_id = %s AND passageiro_id = %s AND status IN ('PENDENTE', 'CONFIRMADA')""",
        (carona_id, usuario["id"]),
    ).fetchone()
    if ja_tem:
        raise HTTPException(409, "Você já tem uma solicitação ativa nesta carona")

    solicitacao = db.execute(
        "INSERT INTO solicitacao (carona_id, passageiro_id) VALUES (%s, %s) RETURNING id",
        (carona_id, usuario["id"]),
    ).fetchone()

    motorista = db.execute(
        "SELECT email FROM usuario WHERE id = %s", (carona["motorista_id"],)
    ).fetchone()
    avisar(
        motorista["email"],
        f"{usuario['nome']} pediu uma vaga na sua carona de {carona['origem']} "
        f"para {carona['destino']}.",
    )
    return {"mensagem": "Solicitação enviada! Aguarde a resposta do motorista.", "id": solicitacao["id"]}


# ---------------------------------------------------------------- US04

def _carregar_solicitacao_do_motorista(db, solicitacao_id: int, usuario: dict):
    """Trava a carona, confere que o usuário é o motorista e devolve (solicitação, carona)."""
    achada = db.execute(
        "SELECT carona_id FROM solicitacao WHERE id = %s", (solicitacao_id,)
    ).fetchone()
    if achada is None:
        raise HTTPException(404, "Solicitação não encontrada")
    # FOR UPDATE: evita que duas respostas simultâneas usem a mesma vaga
    carona = db.execute(
        "SELECT * FROM carona WHERE id = %s FOR UPDATE", (achada["carona_id"],)
    ).fetchone()
    if carona["motorista_id"] != usuario["id"]:
        raise HTTPException(403, "Apenas o motorista pode responder à solicitação")
    solicitacao = db.execute(
        """SELECT s.id, s.status, s.passageiro_id, p.nome, p.email
           FROM solicitacao s JOIN usuario p ON p.id = s.passageiro_id WHERE s.id = %s""",
        (solicitacao_id,),
    ).fetchone()
    if solicitacao["status"] != "PENDENTE":
        raise HTTPException(409, "Esta solicitação já foi respondida")
    if carona["status"] not in ("ABERTA", "LOTADA"):
        raise HTTPException(409, "Esta carona não está mais disponível")
    return solicitacao, carona


@router.get("/caronas/{carona_id}/solicitacoes")
def ver_solicitacoes(
    carona_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    """Lista os pedidos de uma carona (só o motorista vê)."""
    carona = db.execute("SELECT motorista_id FROM carona WHERE id = %s", (carona_id,)).fetchone()
    if carona is None:
        raise HTTPException(404, "Carona não encontrada")
    if carona["motorista_id"] != usuario["id"]:
        raise HTTPException(403, "Apenas o motorista pode ver as solicitações")
    return db.execute(
        """SELECT s.id, s.status, s.criado_em, p.nome, p.curso,
                  CASE WHEN s.status = 'CONFIRMADA' THEN p.telefone END AS telefone
           FROM solicitacao s JOIN usuario p ON p.id = s.passageiro_id
           WHERE s.carona_id = %s ORDER BY s.id""",  # RN10: telefone só depois do aceite
        (carona_id,),
    ).fetchall()


@router.post("/solicitacoes/{solicitacao_id}/aceitar")
def aceitar_solicitacao(
    solicitacao_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    """RF10 e RF11: o motorista aceita o pedido e a vaga é descontada."""
    solicitacao, carona = _carregar_solicitacao_do_motorista(db, solicitacao_id, usuario)

    if carona["vagas_disponiveis"] < 1:  # RN07
        raise HTTPException(409, "Carona lotada")

    conflito = db.execute(  # RN12
        """SELECT 1 FROM solicitacao s JOIN carona c ON c.id = s.carona_id
           WHERE s.passageiro_id = %s AND s.status = 'CONFIRMADA' AND s.carona_id <> %s
             AND abs(extract(epoch FROM (c.saida_em - %s))) < 3600""",
        (solicitacao["passageiro_id"], carona["id"], carona["saida_em"]),
    ).fetchone()
    if conflito:
        raise HTTPException(
            409, "Este passageiro já tem outra carona confirmada em horário muito próximo"
        )

    db.execute(
        "UPDATE solicitacao SET status = 'CONFIRMADA', respondido_em = %s WHERE id = %s",
        (datetime.now(), solicitacao_id),
    )
    vagas = carona["vagas_disponiveis"] - 1
    db.execute(
        "UPDATE carona SET vagas_disponiveis = %s, status = %s WHERE id = %s",
        (vagas, "LOTADA" if vagas == 0 else carona["status"], carona["id"]),
    )
    avisar(
        solicitacao["email"],
        f"Sua solicitação foi aceita! Telefone do motorista {usuario['nome']}: {usuario['telefone']}",
    )
    return {"mensagem": "Solicitação aceita"}


@router.post("/solicitacoes/{solicitacao_id}/recusar")
def recusar_solicitacao(
    solicitacao_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    """RF10: o motorista recusa o pedido."""
    solicitacao, carona = _carregar_solicitacao_do_motorista(db, solicitacao_id, usuario)
    db.execute(
        "UPDATE solicitacao SET status = 'RECUSADA', respondido_em = %s WHERE id = %s",
        (datetime.now(), solicitacao_id),
    )
    avisar(solicitacao["email"], "Sua solicitação de carona foi recusada.")
    return {"mensagem": "Solicitação recusada"}


# ---------------------------------------------------------------- US05

@router.get("/minhas/oferecidas")
def minhas_oferecidas(usuario=Depends(usuario_logado), db=Depends(db_atualizado)):
    """RF14: caronas que eu ofereci."""
    return db.execute(
        BASE_SELECT.replace(
            "o.nome AS origem,",
            """(SELECT count(*) FROM solicitacao s
                WHERE s.carona_id = c.id AND s.status = 'PENDENTE') AS pendentes,
               o.nome AS origem,""",
        )
        + " WHERE c.motorista_id = %s ORDER BY c.saida_em DESC",
        (usuario["id"],),
    ).fetchall()


@router.get("/minhas/solicitadas")
def minhas_solicitadas(usuario=Depends(usuario_logado), db=Depends(db_atualizado)):
    """RF14: caronas que eu solicitei, com o status do meu pedido."""
    return db.execute(
        """SELECT s.id AS solicitacao_id, s.status AS solicitacao_status,
                  c.id AS carona_id, c.saida_em, c.status AS carona_status,
                  o.nome AS origem, d.nome AS destino, u.nome AS motorista_nome,
                  CASE WHEN s.status = 'CONFIRMADA' THEN u.telefone END AS telefone_motorista
           FROM solicitacao s
           JOIN carona c ON c.id = s.carona_id
           JOIN usuario u ON u.id = c.motorista_id
           JOIN local o ON o.id = c.origem_id
           JOIN local d ON d.id = c.destino_id
           WHERE s.passageiro_id = %s ORDER BY c.saida_em DESC, s.id DESC""",
        (usuario["id"],),
    ).fetchall()


@router.post("/solicitacoes/{solicitacao_id}/cancelar")
def cancelar_solicitacao(
    solicitacao_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)
):
    """RF12: o passageiro cancela o pedido."""
    achada = db.execute(
        "SELECT carona_id FROM solicitacao WHERE id = %s", (solicitacao_id,)
    ).fetchone()
    if achada is None:
        raise HTTPException(404, "Solicitação não encontrada")
    carona = db.execute(
        BASE_SELECT + " WHERE c.id = %s FOR UPDATE OF c", (achada["carona_id"],)
    ).fetchone()
    solicitacao = db.execute(
        "SELECT id, status, passageiro_id FROM solicitacao WHERE id = %s", (solicitacao_id,)
    ).fetchone()
    if solicitacao["passageiro_id"] != usuario["id"]:
        raise HTTPException(403, "Você só pode cancelar as suas próprias solicitações")
    if solicitacao["status"] not in ("PENDENTE", "CONFIRMADA"):
        raise HTTPException(409, "Esta solicitação não pode mais ser cancelada")
    if prazo_de_cancelamento_encerrado(carona["saida_em"]):  # RN08
        raise HTTPException(409, "Prazo de cancelamento encerrado")

    db.execute(
        "UPDATE solicitacao SET status = 'CANCELADA', respondido_em = %s WHERE id = %s",
        (datetime.now(), solicitacao_id),
    )
    if solicitacao["status"] == "CONFIRMADA":  # a vaga volta a ficar livre
        db.execute(
            """UPDATE carona SET vagas_disponiveis = vagas_disponiveis + 1,
                      status = CASE WHEN status = 'LOTADA' THEN 'ABERTA' ELSE status END
               WHERE id = %s""",
            (carona["id"],),
        )
    motorista = db.execute(
        "SELECT email FROM usuario WHERE id = %s", (carona["motorista_id"],)
    ).fetchone()
    avisar(
        motorista["email"],
        f"{usuario['nome']} cancelou a solicitação na sua carona de {carona['origem']} "
        f"para {carona['destino']}.",
    )
    return {"mensagem": "Solicitação cancelada"}


@router.post("/caronas/{carona_id}/cancelar")
def cancelar_carona(carona_id: int, usuario=Depends(usuario_logado), db=Depends(db_atualizado)):
    """RF13: o motorista cancela a carona."""
    carona = db.execute(
        BASE_SELECT + " WHERE c.id = %s FOR UPDATE OF c", (carona_id,)
    ).fetchone()
    if carona is None:
        raise HTTPException(404, "Carona não encontrada")
    if carona["motorista_id"] != usuario["id"]:
        raise HTTPException(403, "Apenas o motorista pode cancelar a carona")
    if carona["status"] not in ("ABERTA", "LOTADA"):
        raise HTTPException(409, "Esta carona não pode mais ser cancelada")
    if prazo_de_cancelamento_encerrado(carona["saida_em"]):  # RN08
        raise HTTPException(409, "Prazo de cancelamento encerrado")

    db.execute("UPDATE carona SET status = 'CANCELADA' WHERE id = %s", (carona_id,))
    # RN09: todas as solicitações pendentes e confirmadas também são canceladas
    afetados = db.execute(
        """UPDATE solicitacao s SET status = 'CANCELADA', respondido_em = %s
           FROM usuario p
           WHERE s.carona_id = %s AND s.status IN ('PENDENTE', 'CONFIRMADA')
             AND p.id = s.passageiro_id
           RETURNING p.email""",
        (datetime.now(), carona_id),
    ).fetchall()
    for passageiro in afetados:
        avisar(
            passageiro["email"],
            f"A carona de {carona['origem']} para {carona['destino']} foi cancelada pelo motorista.",
        )
    return {"mensagem": "Carona cancelada"}
