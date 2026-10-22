"""US01 - Cadastro, confirmação de e-mail e login (RF01, RF02, RF03, RN01, RNF07)."""
import uuid

from tests.conftest import SENHA, sql


def dados(**extra):
    base = {"nome": "Ana Souza", "email": f"teste.{uuid.uuid4().hex[:8]}@univille.br",
            "curso": "Direito", "telefone": "(47) 98888-7777", "senha": SENHA}
    base.update(extra)
    return base


def test_cadastro_valido_devolve_link_de_confirmacao(cliente):
    r = cliente.post("/auth/cadastro", json=dados())
    assert r.status_code == 201
    assert "confirmacao" in r.json()["link_confirmacao"] or "token=" in r.json()["link_confirmacao"]


def test_login_so_depois_de_confirmar_o_email(cliente):
    d = dados()
    link = cliente.post("/auth/cadastro", json=d).json()["link_confirmacao"]
    r = cliente.post("/auth/login", json={"email": d["email"], "senha": SENHA})
    assert r.status_code == 403 and r.json()["detail"] == "Confirme seu e-mail"
    assert cliente.get(link.replace("http://localhost:8000", "")).status_code == 200
    r = cliente.post("/auth/login", json={"email": d["email"], "senha": SENHA})
    assert r.status_code == 200 and r.json()["token"]


def test_email_fora_do_dominio_institucional_e_recusado_rn01(cliente):
    r = cliente.post("/auth/cadastro", json=dados(email="teste.alguem@gmail.com"))
    assert r.status_code == 422 and r.json()["detail"] == "Use seu e-mail institucional"


def test_email_duplicado_e_recusado(cliente):
    d = dados()
    assert cliente.post("/auth/cadastro", json=d).status_code == 201
    r = cliente.post("/auth/cadastro", json=d)
    assert r.status_code == 409 and r.json()["detail"] == "E-mail já cadastrado"


def test_senha_e_guardada_com_hash(cliente):
    d = dados()
    cliente.post("/auth/cadastro", json=d)
    hash_salvo = sql("SELECT senha_hash FROM usuario WHERE email = %s", (d["email"],))[0][0]
    assert hash_salvo != SENHA and hash_salvo.startswith("$2")


def test_validacoes_dos_campos_do_cadastro(cliente):
    casos = [
        ({"senha": "curta"}, "A senha deve ter no mínimo 8 caracteres"),
        ({"email": "sem-arroba"}, "E-mail inválido"),
        ({"nome": " "}, "Informe o nome"),
        ({"curso": ""}, "Informe o curso"),
        ({"telefone": "123"}, None),
        ({"telefone": "(47) 9 9999-99999999"}, None),
    ]
    for extra, msg in casos:
        r = cliente.post("/auth/cadastro", json=dados(**extra))
        assert r.status_code == 422, extra
        if msg:
            assert r.json()["detail"] == msg


def test_cadastro_com_campos_faltando(cliente):
    r = cliente.post("/auth/cadastro", json={"email": "teste.x@univille.br"})
    assert r.status_code == 422 and r.json()["detail"] == "Preencha todos os campos"


def test_telefone_aceita_10_ou_11_digitos_em_qualquer_formato(cliente):
    for tel in ("4799998888", "47999998888", "(47) 9999-8888"):
        assert cliente.post("/auth/cadastro", json=dados(telefone=tel)).status_code == 201, tel


def test_link_de_confirmacao_invalido(cliente):
    r = cliente.get("/auth/confirmar-email", params={"token": "lixo"})
    assert r.status_code == 400


def test_token_de_acesso_nao_serve_como_link_de_confirmacao(novo_usuario, cliente):
    u = novo_usuario()
    token = u.headers["Authorization"].split()[1]
    assert cliente.get("/auth/confirmar-email", params={"token": token}).status_code == 400


def test_login_com_senha_errada_e_email_inexistente(novo_usuario, cliente):
    u = novo_usuario()
    r = cliente.post("/auth/login", json={"email": u.email, "senha": "errada123"})
    assert r.status_code == 401 and r.json()["detail"] == "E-mail ou senha incorretos"
    r = cliente.post("/auth/login", json={"email": "teste.naoexiste@univille.br", "senha": SENHA})
    assert r.status_code == 401


def test_cinco_senhas_erradas_bloqueiam_o_login_rnf07(novo_usuario, cliente):
    u = novo_usuario()
    for _ in range(5):
        assert cliente.post("/auth/login", json={"email": u.email, "senha": "errada123"}).status_code == 401
    # agora até a senha certa é bloqueada
    r = cliente.post("/auth/login", json={"email": u.email, "senha": SENHA})
    assert r.status_code == 429 and "bloqueado" in r.json()["detail"]


def test_login_certo_zera_o_contador_de_erros(novo_usuario, cliente):
    u = novo_usuario()
    for _ in range(4):
        cliente.post("/auth/login", json={"email": u.email, "senha": "errada123"})
    assert cliente.post("/auth/login", json={"email": u.email, "senha": SENHA}).status_code == 200
    for _ in range(4):
        assert cliente.post("/auth/login", json={"email": u.email, "senha": "errada123"}).status_code == 401


def test_rotas_protegidas_exigem_login(cliente):
    for metodo, url in [("get", "/perfil"), ("get", "/minhas/oferecidas"), ("post", "/caronas"),
                        ("get", "/veiculos")]:
        assert getattr(cliente, metodo)(url).status_code == 401, url
    r = cliente.get("/perfil", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401
