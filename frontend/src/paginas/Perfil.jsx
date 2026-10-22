import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, apagarToken } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Campo } from "../componentes/Campos.jsx";
import {
  MSG_PLACA, MSG_TELEFONE, mascaraPlaca, mascaraTelefone, placaParaTela, placaValida, telefoneParaTela, telefoneValido,
} from "../util";

// Tela 08 - Perfil e veículo (US06, RF04 e RF05)
export default function Perfil() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null);
  const [nome, setNome] = useState("");
  const [curso, setCurso] = useState("");
  const [telefone, setTelefone] = useState("");
  const [veiculo, setVeiculo] = useState(null); // primeiro veículo do usuário, se existir
  const [editandoVeiculo, setEditandoVeiculo] = useState(false);
  const [formVeiculo, setFormVeiculo] = useState({ modelo: "", cor: "", placa: "", lugares: 4 });
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    async function carregar() {
      try {
        const eu = await api.get("/perfil");
        setUsuario(eu);
        setNome(eu.nome);
        setCurso(eu.curso);
        setTelefone(telefoneParaTela(eu.telefone));
        const veiculos = await api.get("/veiculos");
        setVeiculo(veiculos[0] || null);
      } catch (e) {
        setErro(e.message);
      }
    }
    carregar();
  }, []);

  async function salvar() {
    setErro("");
    setAviso("");
    if (nome.trim().length < 2) return setErro("Informe o nome");
    if (curso.trim().length < 2) return setErro("Informe o curso");
    if (!telefoneValido(telefone)) return setErro(MSG_TELEFONE);
    try {
      const r = await api.put("/perfil", { nome, curso, telefone });
      setUsuario({ ...usuario, nome: nome.trim() });
      setAviso(r.mensagem);
    } catch (e) {
      setErro(e.message);
    }
  }

  function abrirFormVeiculo() {
    if (veiculo) setFormVeiculo({ modelo: veiculo.modelo, cor: veiculo.cor, placa: veiculo.placa, lugares: veiculo.lugares });
    setEditandoVeiculo(true);
  }

  async function salvarVeiculo() {
    setErro("");
    setAviso("");
    if (!placaValida(formVeiculo.placa)) return setErro(MSG_PLACA);
    const corpo = { ...formVeiculo, lugares: Number(formVeiculo.lugares) };
    try {
      const salvo = veiculo ? await api.put(`/veiculos/${veiculo.id}`, corpo) : await api.post("/veiculos", corpo);
      setVeiculo(salvo);
      setEditandoVeiculo(false);
      setAviso("Veículo salvo com sucesso");
    } catch (e) {
      setErro(e.message);
    }
  }

  function sair() {
    apagarToken();
    navigate("/login");
  }

  if (!usuario) {
    return (
      <Tela titulo="Perfil" menu="perfil">
        {erro ? <p className="erro">{erro}</p> : <p className="vazio">Carregando...</p>}
      </Tela>
    );
  }

  return (
    <Tela titulo="Perfil" menu="perfil">
      <div className="perfil-topo">
        <div className="avatar" />
        <div>
          <p className="perfil-nome">{usuario.nome}</p>
          <p className="perfil-email">{usuario.email}</p>
        </div>
      </div>
      <Campo rotulo="Nome completo">
        <input className="entrada" value={nome} onChange={(e) => setNome(e.target.value)} />
      </Campo>
      <Campo rotulo="Curso">
        <input className="entrada" value={curso} onChange={(e) => setCurso(e.target.value)} />
      </Campo>
      <Campo rotulo="Telefone (WhatsApp)">
        <input className="entrada" type="tel" inputMode="numeric" maxLength={16} placeholder="(47) 9 9999-9999" value={telefone} onChange={(e) => setTelefone(mascaraTelefone(e.target.value))} />
      </Campo>

      <div className="cartao">
        <div className="veiculo-titulo">
          <p>Meu veículo</p>
          {!editandoVeiculo && <button onClick={abrirFormVeiculo}>{veiculo ? "Alterar" : "Cadastrar"}</button>}
        </div>
        {editandoVeiculo ? (
          <>
            <Campo rotulo="Modelo">
              <input className="entrada" placeholder="Ex.: Fiat Argo" value={formVeiculo.modelo} onChange={(e) => setFormVeiculo({ ...formVeiculo, modelo: e.target.value })} />
            </Campo>
            <Campo rotulo="Cor">
              <input className="entrada" placeholder="Ex.: Prata" value={formVeiculo.cor} onChange={(e) => setFormVeiculo({ ...formVeiculo, cor: e.target.value })} />
            </Campo>
            <Campo rotulo="Placa">
              <input className="entrada" placeholder="Ex.: ABC1D23" maxLength={8} value={formVeiculo.placa} onChange={(e) => setFormVeiculo({ ...formVeiculo, placa: mascaraPlaca(e.target.value) })} />
            </Campo>
            <Campo rotulo="Lugares (2 a 8)">
              <input className="entrada" type="number" min="2" max="8" value={formVeiculo.lugares} onChange={(e) => setFormVeiculo({ ...formVeiculo, lugares: e.target.value })} />
            </Campo>
            <div className="acoes">
              <button className="botao botao-contorno" onClick={() => setEditandoVeiculo(false)}>Cancelar</button>
              <button className="botao" onClick={salvarVeiculo}>Salvar veículo</button>
            </div>
          </>
        ) : (
          <p className="veiculo-texto">
            {veiculo
              ? `${veiculo.modelo} · ${veiculo.cor} · ${placaParaTela(veiculo.placa)} · ${veiculo.lugares} lugares`
              : "Nenhum veículo cadastrado"}
          </p>
        )}
      </div>

      {erro && <p className="erro">{erro}</p>}
      {aviso && <p className="sucesso">{aviso}</p>}
      <button className="botao" onClick={salvar}>Salvar alterações</button>
      <button className="botao botao-perigo" onClick={sair}>Sair</button>
    </Tela>
  );
}
