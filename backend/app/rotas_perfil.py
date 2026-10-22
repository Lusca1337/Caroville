"""US06 - Perfil e veículo (RF04, RF05) e lista de locais."""
import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.db import get_db
from app.modelos import PerfilEdicao, VeiculoDados
from app.seguranca import usuario_logado

router = APIRouter(tags=["Perfil e veículo"])


@router.get("/perfil")
def ver_perfil(usuario=Depends(usuario_logado)):
    return usuario


@router.put("/perfil")
def editar_perfil(dados: PerfilEdicao, usuario=Depends(usuario_logado), db=Depends(get_db)):
    db.execute(
        "UPDATE usuario SET nome = %s, curso = %s, telefone = %s WHERE id = %s",
        (dados.nome, dados.curso, dados.telefone, usuario["id"]),
    )
    return {"mensagem": "Dados salvos com sucesso"}


@router.get("/veiculos")
def listar_veiculos(usuario=Depends(usuario_logado), db=Depends(get_db)):
    return db.execute(
        "SELECT id, modelo, cor, placa, lugares FROM veiculo WHERE usuario_id = %s ORDER BY id",
        (usuario["id"],),
    ).fetchall()


@router.post("/veiculos", status_code=201)
def criar_veiculo(dados: VeiculoDados, usuario=Depends(usuario_logado), db=Depends(get_db)):
    try:
        veiculo = db.execute(
            """INSERT INTO veiculo (usuario_id, modelo, cor, placa, lugares)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, modelo, cor, placa, lugares""",
            (usuario["id"], dados.modelo, dados.cor, dados.placa, dados.lugares),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Esta placa já está cadastrada")
    return veiculo


@router.put("/veiculos/{veiculo_id}")
def editar_veiculo(
    veiculo_id: int, dados: VeiculoDados, usuario=Depends(usuario_logado), db=Depends(get_db)
):
    try:
        veiculo = db.execute(
            """UPDATE veiculo SET modelo = %s, cor = %s, placa = %s, lugares = %s
               WHERE id = %s AND usuario_id = %s RETURNING id, modelo, cor, placa, lugares""",
            (dados.modelo, dados.cor, dados.placa, dados.lugares, veiculo_id, usuario["id"]),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Esta placa já está cadastrada")
    if veiculo is None:
        raise HTTPException(404, "Veículo não encontrado")
    return veiculo


@router.delete("/veiculos/{veiculo_id}")
def excluir_veiculo(veiculo_id: int, usuario=Depends(usuario_logado), db=Depends(get_db)):
    try:
        removido = db.execute(
            "DELETE FROM veiculo WHERE id = %s AND usuario_id = %s RETURNING id",
            (veiculo_id, usuario["id"]),
        ).fetchone()
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(409, "Este veículo já foi usado em caronas e não pode ser excluído")
    if removido is None:
        raise HTTPException(404, "Veículo não encontrado")
    return {"mensagem": "Veículo excluído"}


@router.get("/locais")
def listar_locais(db=Depends(get_db)):
    return db.execute("SELECT id, nome, tipo FROM local ORDER BY tipo DESC, nome").fetchall()
