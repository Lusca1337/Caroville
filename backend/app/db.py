"""Conexão com o PostgreSQL. Cada requisição usa uma conexão (e uma transação)."""
import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


def get_db():
    # Se a rota terminar bem, a transação é confirmada; se der erro, é desfeita.
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn
