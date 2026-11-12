"""Configurações lidas das variáveis de ambiente (arquivo .env)."""
import os
from dotenv import load_dotenv

load_dotenv()

# VULN-02/03: sem valores padrão. Se faltar ou estiver fraco, o servidor não sobe.
DATABASE_URL = os.getenv("DATABASE_URL", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "120"))

# RN01
DOMINIO_EMAIL = "@univille.br"

# RNF07: 5 senhas erradas seguidas bloqueiam o login por 15 minutos
MAX_TENTATIVAS = 5
MINUTOS_BLOQUEIO = 15

# VULN-01/07: modo demonstração. Só com MODO_DEMO=true a API devolve o link de
# confirmação no cadastro e expõe a documentação (/docs). Em produção deve ser false.
MODO_DEMO = os.getenv("MODO_DEMO", "false").strip().lower() == "true"

# Valores de exemplo que já estiveram no código ou no .env.example (são públicos)
_CHAVES_CONHECIDAS = ("chave-apenas-para-desenvolvimento", "troque-esta-chave")

if not DATABASE_URL:
    raise RuntimeError("Defina DATABASE_URL no arquivo .env (veja .env.example)")
if len(SECRET_KEY) < 32 or SECRET_KEY.startswith(_CHAVES_CONHECIDAS):
    raise RuntimeError(
        "SECRET_KEY ausente, curta (mínimo 32 caracteres) ou de exemplo. Gere uma com: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )
