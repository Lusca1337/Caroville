import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import Tela from "../componentes/Tela.jsx";
import { ChipStatus } from "../componentes/Campos.jsx";
import { dataEHora, nomeAbreviado } from "../util";

// Tela 07 - Solicitações recebidas (US04, RF10 e RF11)
export default function Solicitacoes() {
  const { id } = useParams();
  const [carona, setCarona] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [carregando, setCarregando] = useState(true);
  const [respondendo, setRespondendo] = useState(null); // id do pedido sendo respondido

  async function carregar() {
    try {
      setCarona(await api.get(`/caronas/${id}`));
      setPedidos(await api.get(`/caronas/${id}/solicitacoes`));
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }
  useEffect(() => { carregar(); }, [id]);

  async function responder(pedidoId, acao) {
    setErro("");
    setAviso("");
    setRespondendo(pedidoId);
    try {
      const r = await api.post(`/solicitacoes/${pedidoId}/${acao}`);
      setAviso(r.mensagem);
      await carregar();
    } catch (e) {
      setErro(e.message); // ex.: "Carona lotada"
    } finally {
      setRespondendo(null);
    }
  }

  return (
    <Tela titulo="Solicitações" menu="minhas">
      {carona && (
        <p className="resumo">{dataEHora(carona.saida_em)} · {carona.origem} → {carona.destino}</p>
      )}
      {carregando && <p className="vazio">Carregando...</p>}
      {erro && <p className="erro">{erro}</p>}
      {aviso && <p className="sucesso">{aviso}</p>}
      {carona && pedidos.length === 0 && <p className="vazio">Nenhuma solicitação ainda</p>}
      {pedidos.map((p) => (
        <div key={p.id} className="cartao">
          <div className="cartao-topo">
            <p className="hora">{nomeAbreviado(p.nome)}</p>
            <ChipStatus status={p.status} />
          </div>
          <p className="detalhe">{p.curso} · quer 1 vaga</p>
          {p.telefone && <p className="detalhe">Telefone: {p.telefone}</p>}
          {p.status === "PENDENTE" && (
            <div className="acoes">
              <button className="botao botao-perigo" disabled={respondendo !== null} onClick={() => responder(p.id, "recusar")}>Recusar</button>
              <button className="botao" disabled={respondendo !== null} onClick={() => responder(p.id, "aceitar")}>
                {respondendo === p.id ? "Enviando..." : "Aceitar"}
              </button>
            </div>
          )}
        </div>
      ))}
    </Tela>
  );
}
