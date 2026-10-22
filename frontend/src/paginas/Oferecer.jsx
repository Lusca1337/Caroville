import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Campo } from "../componentes/Campos.jsx";
import Trajeto from "../componentes/Trajeto.jsx";
import { agoraParaCampo, horarioPadrao } from "../util";

// Tela 05 - Oferecer carona (US02, RF06)
export default function Oferecer() {
  const navigate = useNavigate();
  const [locais, setLocais] = useState([]);
  const [dados, setDados] = useState({
    origem_id: "",
    destino_id: "",
    saida_em: horarioPadrao(),
    vagas_total: 3,
    ponto_encontro: "",
    observacoes: "",
  });
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  const mudar = (campo) => (e) => setDados({ ...dados, [campo]: e.target.value });

  useEffect(() => {
    api.get("/locais").then((lista) => {
      setLocais(lista);
      const campus = lista.find((l) => l.tipo === "CAMPUS");
      if (campus) setDados((d) => ({ ...d, destino_id: String(campus.id) }));
    }).catch((e) => setErro(e.message));
  }, []);

  async function publicar(evento) {
    evento.preventDefault();
    setErro("");
    if (!dados.origem_id || !dados.destino_id) return setErro("Escolha o local de saída e o destino");
    // RN04: a carona precisa ser de hoje em diante, com pelo menos 1 hora de antecedência
    if (dados.saida_em < agoraParaCampo(1)) return setErro("Informe um horário futuro, com pelo menos 1 hora de antecedência");
    setEnviando(true);
    try {
      await api.post("/caronas", {
        origem_id: Number(dados.origem_id),
        destino_id: Number(dados.destino_id),
        saida_em: dados.saida_em,
        vagas_total: Number(dados.vagas_total),
        ponto_encontro: dados.ponto_encontro,
        observacoes: dados.observacoes,
      });
      navigate("/minhas");
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Tela titulo="Oferecer carona" menu="oferecer">
      <form className="formulario" onSubmit={publicar}>
        <Trajeto
          locais={locais}
          origemId={dados.origem_id}
          destinoId={dados.destino_id}
          rotuloOrigem="Local de saída"
          aoMudar={(origem, destino) => setDados({ ...dados, origem_id: origem, destino_id: destino })}
        />
        <Campo rotulo="Data e horário">
          <input className="entrada" type="datetime-local" min={agoraParaCampo(1)} value={dados.saida_em} onChange={mudar("saida_em")} required />
        </Campo>
        <Campo rotulo="Número de vagas">
          <input className="entrada" type="number" min="1" max="4" value={dados.vagas_total} onChange={mudar("vagas_total")} required />
        </Campo>
        <Campo rotulo="Ponto de encontro (opcional)">
          <input className="entrada" placeholder="Ex.: Praça da Bandeira" value={dados.ponto_encontro} onChange={mudar("ponto_encontro")} />
        </Campo>
        <Campo rotulo="Observações (opcional)">
          <input className="entrada" value={dados.observacoes} onChange={mudar("observacoes")} />
        </Campo>
        {erro && <p className="erro">{erro}</p>}
        {erro.includes("veículo") && <Link className="link" to="/perfil">Cadastrar veículo no perfil</Link>}
        <button className="botao" type="submit" disabled={enviando}>
          {enviando ? "Publicando..." : "Publicar carona"}
        </button>
      </form>
    </Tela>
  );
}
