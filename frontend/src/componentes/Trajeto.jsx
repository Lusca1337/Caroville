import { Campo } from "./Campos.jsx";

// Campos de saída e destino.
// Regra do projeto: toda carona liga o Campus Univille a um bairro (nunca bairro com bairro).
// A saída é livre. Quem escolhe um bairro na saída só pode escolher o campus no destino
// (e quem sai do campus só pode ir para um bairro). Se der conflito, o destino se ajusta sozinho.
export default function Trajeto({ locais, origemId, destinoId, aoMudar, rotuloOrigem = "Saída" }) {
  const tipo = (id) => locais.find((l) => String(l.id) === String(id))?.tipo; // "CAMPUS" ou "BAIRRO"
  const campus = locais.find((l) => l.tipo === "CAMPUS");

  // Opções do destino: só locais de tipo diferente do local de saída
  const opcoes = (outroId) => (tipo(outroId) ? locais.filter((l) => l.tipo !== tipo(outroId)) : locais);

  // Depois de escolher "id" de um lado, devolve o valor certo para o outro lado
  function ajustar(id, outroId) {
    if (!tipo(id)) return outroId; // nada escolhido
    if (!outroId || tipo(outroId) === tipo(id)) {
      return tipo(id) === "BAIRRO" ? String(campus.id) : ""; // bairro -> campus; campus -> escolher o bairro
    }
    return outroId;
  }

  return (
    <>
      <Campo rotulo={rotuloOrigem}>
        <select
          className="entrada"
          value={origemId}
          onChange={(e) => aoMudar(e.target.value, ajustar(e.target.value, destinoId))}
        >
          <option value="">Selecione</option>
          {locais.map((l) => <option key={l.id} value={l.id}>{l.nome}</option>)}
        </select>
      </Campo>
      <Campo rotulo="Destino">
        <select
          className="entrada"
          value={destinoId}
          onChange={(e) => aoMudar(ajustar(e.target.value, origemId), e.target.value)}
        >
          <option value="">Selecione</option>
          {opcoes(origemId).map((l) => <option key={l.id} value={l.id}>{l.nome}</option>)}
        </select>
      </Campo>
    </>
  );
}
