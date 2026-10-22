import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, guardarToken } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Campo } from "../componentes/Campos.jsx";

// Tela 01 - Login (US01, RF03)
export default function Login() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();

  async function entrar(evento) {
    evento.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      const { token } = await api.post("/auth/login", { email, senha });
      guardarToken(token);
      navigate("/");
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Tela titulo="Caroville">
      <form className="formulario" onSubmit={entrar}>
        <h2 className="titulo">Bem-vindo de volta</h2>
        <p className="subtitulo">Entre com seu e-mail institucional da Univille.</p>
        <Campo rotulo="E-mail institucional">
          <input
            className="entrada"
            type="email"
            placeholder="aluno@univille.br"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </Campo>
        <Campo rotulo="Senha">
          <input
            className="entrada"
            type="password"
            placeholder="••••••••"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />
        </Campo>
        {erro && <p className="erro">{erro}</p>}
        <button className="botao" type="submit" disabled={enviando}>
          {enviando ? "Entrando..." : "Entrar"}
        </button>
        <Link className="botao botao-contorno" to="/cadastro">
          Criar conta
        </Link>
      </form>
    </Tela>
  );
}
