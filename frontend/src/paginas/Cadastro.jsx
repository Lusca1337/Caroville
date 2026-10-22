import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, confirmarEmail } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Campo } from "../componentes/Campos.jsx";
import { MSG_TELEFONE, mascaraTelefone, telefoneValido } from "../util";

// Tela 02 - Cadastro (US01, RF01 e RF02)
export default function Cadastro() {
  const [dados, setDados] = useState({ nome: "", email: "", curso: "", telefone: "", senha: "" });
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [link, setLink] = useState(""); // link de confirmação devolvido pela API
  const [confirmado, setConfirmado] = useState(false);
  const navigate = useNavigate();

  const mudar = (campo) => (e) => setDados({ ...dados, [campo]: e.target.value });

  async function cadastrar(evento) {
    evento.preventDefault();
    setErro("");
    if (!telefoneValido(dados.telefone)) return setErro(MSG_TELEFONE);
    setEnviando(true);
    try {
      const resposta = await api.post("/auth/cadastro", dados);
      setLink(resposta.link_confirmacao);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  // No MVP o e-mail é simulado: este botão faz o papel de "clicar no link do e-mail"
  async function confirmar() {
    setErro("");
    try {
      await confirmarEmail(link);
      setConfirmado(true);
    } catch (e) {
      setErro(e.message);
    }
  }

  // Depois de criar a conta, pede a confirmação do e-mail
  if (link) {
    return (
      <Tela titulo="Criar conta">
        <h2 className="titulo">Confirme seu e-mail</h2>
        <p className="subtitulo">
          Enviamos um link de confirmação para {dados.email}. Como o envio de e-mail é simulado
          neste projeto, use o botão abaixo para confirmar.
        </p>
        {erro && <p className="erro">{erro}</p>}
        {confirmado ? (
          <>
            <p className="sucesso">E-mail confirmado! Agora você já pode entrar.</p>
            <button className="botao" onClick={() => navigate("/login")}>
              Ir para o login
            </button>
          </>
        ) : (
          <button className="botao" onClick={confirmar}>
            Confirmar e-mail
          </button>
        )}
      </Tela>
    );
  }

  return (
    <Tela titulo="Criar conta">
      <form className="formulario" onSubmit={cadastrar}>
        <Campo rotulo="Nome completo">
          <input className="entrada" placeholder="Seu nome" value={dados.nome} onChange={mudar("nome")} required />
        </Campo>
        <Campo rotulo="E-mail institucional">
          <input className="entrada" type="email" placeholder="aluno@univille.br" value={dados.email} onChange={mudar("email")} required />
        </Campo>
        <Campo rotulo="Curso">
          <input className="entrada" placeholder="Ex.: Ciência da Computação" value={dados.curso} onChange={mudar("curso")} required />
        </Campo>
        <Campo rotulo="Telefone (WhatsApp)">
          <input className="entrada" type="tel" inputMode="numeric" maxLength={16} placeholder="(47) 9 9999-9999" value={dados.telefone} onChange={(e) => setDados({ ...dados, telefone: mascaraTelefone(e.target.value) })} required />
        </Campo>
        <Campo rotulo="Senha">
          <input className="entrada" type="password" placeholder="Mínimo 8 caracteres" value={dados.senha} onChange={mudar("senha")} required />
        </Campo>
        {erro && <p className="erro">{erro}</p>}
        <button className="botao" type="submit" disabled={enviando}>
          {enviando ? "Criando..." : "Criar conta"}
        </button>
        <Link className="link" to="/login">
          Já tenho conta
        </Link>
      </form>
    </Tela>
  );
}
