"""Formato e validação dos dados que chegam na API (mensagens em português)."""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.config import DOMINIO_EMAIL


def _texto(valor: str, campo: str, minimo: int, maximo: int) -> str:
    valor = (valor or "").strip()
    if len(valor) < minimo:
        raise ValueError(f"Informe {campo}")
    if len(valor) > maximo:
        raise ValueError(f"{campo.capitalize()} deve ter no máximo {maximo} caracteres")
    return valor


def _telefone(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) not in (10, 11):
        raise ValueError("Telefone inválido. Use DDD + número, ex.: (47) 90000-0000")
    return valor.strip()


class Cadastro(BaseModel):
    nome: str
    email: str
    curso: str
    telefone: str
    senha: str

    @field_validator("nome")
    @classmethod
    def v_nome(cls, v):
        return _texto(v, "o nome", 2, 100)

    @field_validator("email")
    @classmethod
    def v_email(cls, v):
        v = (v or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("E-mail inválido")
        if not v.endswith(DOMINIO_EMAIL):  # RN01
            raise ValueError("Use seu e-mail institucional")
        return v

    @field_validator("curso")
    @classmethod
    def v_curso(cls, v):
        return _texto(v, "o curso", 2, 100)

    @field_validator("telefone")
    @classmethod
    def v_telefone(cls, v):
        return _telefone(v)

    @field_validator("senha")
    @classmethod
    def v_senha(cls, v):
        if len(v or "") < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres")
        return v


class Login(BaseModel):
    email: str
    senha: str

    @field_validator("email")
    @classmethod
    def v_email(cls, v):
        return (v or "").strip().lower()


class PerfilEdicao(BaseModel):
    nome: str
    curso: str
    telefone: str

    @field_validator("nome")
    @classmethod
    def v_nome(cls, v):
        return _texto(v, "o nome", 2, 100)

    @field_validator("curso")
    @classmethod
    def v_curso(cls, v):
        return _texto(v, "o curso", 2, 100)

    @field_validator("telefone")
    @classmethod
    def v_telefone(cls, v):
        return _telefone(v)


class VeiculoDados(BaseModel):
    modelo: str
    cor: str
    placa: str
    lugares: int

    @field_validator("modelo")
    @classmethod
    def v_modelo(cls, v):
        return _texto(v, "o modelo do veículo", 2, 60)

    @field_validator("cor")
    @classmethod
    def v_cor(cls, v):
        return _texto(v, "a cor do veículo", 2, 30)

    @field_validator("placa")
    @classmethod
    def v_placa(cls, v):
        # Guarda sem hífen e em maiúsculas: "abc-1234" vira "ABC1234"
        v = re.sub(r"[\s-]", "", v or "").upper()
        if not re.fullmatch(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", v):
            raise ValueError("Placa inválida. Use ABC-1234 ou ABC1D23")
        return v

    @field_validator("lugares")
    @classmethod
    def v_lugares(cls, v):
        if not 2 <= v <= 8:
            raise ValueError("O veículo deve ter entre 2 e 8 lugares")
        return v


class CaronaNova(BaseModel):
    veiculo_id: Optional[int] = None  # se não vier, usa o primeiro veículo do motorista
    origem_id: int
    destino_id: int
    saida_em: datetime
    vagas_total: int
    ponto_encontro: Optional[str] = None
    observacoes: Optional[str] = None

    @field_validator("saida_em")
    @classmethod
    def v_saida(cls, v):
        # Se vier com fuso horário, converte para o horário local (sem fuso)
        if v.tzinfo is not None:
            v = v.astimezone().replace(tzinfo=None)
        return v

    @field_validator("vagas_total")
    @classmethod
    def v_vagas(cls, v):  # RN03
        if not 1 <= v <= 4:
            raise ValueError("O número de vagas deve ser de 1 a 4")
        return v

    @field_validator("ponto_encontro")
    @classmethod
    def v_ponto(cls, v):
        v = (v or "").strip()
        if len(v) > 120:
            raise ValueError("O ponto de encontro deve ter no máximo 120 caracteres")
        return v or None

    @field_validator("observacoes")
    @classmethod
    def v_obs(cls, v):
        v = (v or "").strip()
        if len(v) > 255:
            raise ValueError("As observações devem ter no máximo 255 caracteres")
        return v or None

    @model_validator(mode="after")
    def v_origem_destino(self):
        if self.origem_id == self.destino_id:
            raise ValueError("Saída e destino devem ser diferentes")
        return self
