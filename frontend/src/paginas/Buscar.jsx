import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Campo, Chip } from "../componentes/Campos.jsx";
import Trajeto from "../componentes/Trajeto.jsx";
import { hojeParaCampo, horaCurta, nomeAbreviado, textoVagas } from "../util";

// Tela 03 - Buscar caronas (US03, RF07)
export default function Buscar() {
  const [locais, setLocais] = useState([]);
  const [origemId, setOrigemId] = useState("");
  const [destinoId, setDestinoId] = useState("");
  const [data, setData] = useState(hojeParaCampo());
  const [resultados, setResultados] = useState(null); // null = ainda não buscou
  const [erro, setErro] = useState("");
  const [buscando, setBuscando] = useState(false);

  // Carrega os locais e deixa o Campus Univille como destino inicial
  useEffect(() => {
    api.get("/locais").then((lista) => {
      setLocais(lista);
      const campus = lista.find((l) => l.tipo === "CAMPUS");
      if (campus) setDestinoId(String(campus.id));
    }).catch((e) => setErro(e.message));
  }, []);

  async function buscar(evento) {
    evento.preventDefault();
    setErro("");
    if (!origemId || !destinoId) return setErro("Escolha o local de saída e o destino");
    if (!data) return setErro("Escolha o dia");
    if (data < hojeParaCampo()) return setErro("Escolha um dia de hoje em diante");
    setBuscando(true);
    try {
      const params = new URLSearchParams({ origem_id: origemId, destino_id: destinoId, data });
      setResultados(await api.get("/caronas?" + params));
    } catch (e) {
      setErro(e.message);
    } finally {
      setBuscando(false);
    }
  }

  return (
    <Tela titulo="Buscar caronas" menu="buscar">
      <form className="formulario" onSubmit={buscar}>
        <Trajeto
          locais={locais}
          origemId={origemId}
          destinoId={destinoId}
          aoMudar={(origem, destino) => { setOrigemId(origem); setDestinoId(destino); }}
        />
        <Campo rotulo="Dia">
          <input className="entrada" type="date" min={hojeParaCampo()} value={data} onChange={(e) => setData(e.target.value)} required />
        </Campo>
        {erro && <p className="erro">{erro}</p>}
        <button className="botao" type="submit" disabled={buscando}>
          {buscando ? "Buscando..." : "Buscar caronas"}
        </button>
      </form>

      {resultados && (
        <>
          <h2 className="secao">Resultados</h2>
          {resultados.length === 0 && <p className="vazio">Nenhuma carona encontrada</p>}
          {resultados.map((c) => (
            <Link key={c.id} to={`/carona/${c.id}`} className="cartao">
              <div className="cartao-topo">
                <p className="hora">{horaCurta(c.saida_em)}</p>
                <Chip>{textoVagas(c.vagas_disponiveis)}</Chip>
              </div>
              <p className="rota">{c.origem}  →  {c.destino}</p>
              <p className="detalhe">{c.rua}</p>
              <p className="detalhe">{nomeAbreviado(c.motorista_nome)} · {c.veiculo_modelo}</p>
            </Link>
          ))}
        </>
      )}
    </Tela>
  );
}
