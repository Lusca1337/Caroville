"""Configurações lidas das variáveis de ambiente (arquivo .env)."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/caroville")
SECRET_KEY = os.getenv("SECRET_KEY", "chave-apenas-para-desenvolvimento")
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "120"))

# RN01
DOMINIO_EMAIL = "@univille.br"

# RNF07: 5 senhas erradas seguidas bloqueiam o login por 15 minutos
MAX_TENTATIVAS = 5
MINUTOS_BLOQUEIO = 15
