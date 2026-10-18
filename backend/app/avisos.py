"""Avisos por e-mail. No MVP o e-mail é simulado: a mensagem aparece no terminal do backend."""


def avisar(email: str, texto: str) -> None:
    print(f"[E-MAIL SIMULADO] Para {email}: {texto}")
