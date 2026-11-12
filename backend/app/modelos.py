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


# DDDs que existem no Brasil (qualquer estado, não só o 47 de Joinville)
DDDS_VALIDOS = {
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99,
}


def _telefone(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) not in (10, 11):
        raise ValueError("Telefone inválido. Use DDD + número, ex.: (11) 9 9999-9999")
    if int(digitos[:2]) not in DDDS_VALIDOS:
        raise ValueError("DDD inválido")
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
        if len(v.encode()) > 72:  # VULN-06: limite do bcrypt
            raise ValueError("A senha deve ter no máximo 72 caracteres")
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
    vagas: int  # vagas para passageiros, sem contar o motorista

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

    @field_validator("vagas")
    @classmethod
    def v_vagas(cls, v):  # RN03
        if not 1 <= v <= 4:
            raise ValueError("O veículo deve ter de 1 a 4 vagas para passageiros")
        return v


class CaronaNova(BaseModel):
    veiculo_id: Optional[int] = None  # se não vier, usa o primeiro veículo do motorista
    origem_id: int
    destino_id: int
    saida_em: datetime
    rua: str  # rua no bairro (saída ou chegada), para o passageiro achar a carona
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

    @field_validator("rua")
    @classmethod
    def v_rua(cls, v):
        return _texto(v, "a rua", 3, 120)

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
