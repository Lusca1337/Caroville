import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Chip, ChipStatus } from "../componentes/Campos.jsx";
import { dataEHora, nomeAbreviado, placaParaTela, textoVagas } from "../util";

// Tela 06 - Minhas caronas (US05, RF12, RF13 e RF14)
export default function Minhas() {
  const [aba, setAba] = useState("oferecidas");
  const [oferecidas, setOferecidas] = useState([]);
  const [solicitadas, setSolicitadas] = useState([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    try {
      setOferecidas(await api.get("/minhas/oferecidas"));
      setSolicitadas(await api.get("/minhas/solicitadas"));
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  }
  useEffect(() => { carregar(); }, []);

  async function cancelar(texto, caminho) {
    if (!window.confirm(texto)) return;
    setErro("");
    setAviso("");
    try {
      const r = await api.post(caminho);
      setAviso(r.mensagem);
      carregar();
    } catch (e) {
      setErro(e.message); // ex.: "Prazo de cancelamento encerrado"
    }
  }

  return (
    <Tela titulo="Minhas caronas" menu="minhas">
      <div className="abas">
        <button className={"aba" + (aba === "oferecidas" ? " ativa" : "")} onClick={() => setAba("oferecidas")}>Oferecidas</button>
        <button className={"aba" + (aba === "solicitadas" ? " ativa" : "")} onClick={() => setAba("solicitadas")}>Solicitadas</button>
      </div>
      {erro && <p className="erro">{erro}</p>}
      {aviso && <p className="sucesso">{aviso}</p>}
      {carregando && <p className="vazio">Carregando...</p>}

      {!carregando && aba === "oferecidas" && (
        <>
          {oferecidas.length === 0 && <p className="vazio">Você ainda não ofereceu nenhuma carona</p>}
          {oferecidas.map((c) => {
            const ativa = c.status === "ABERTA" || c.status === "LOTADA";
            const confirmados = c.vagas_total - c.vagas_disponiveis;
            const resumo = [];
            if (c.pendentes > 0) resumo.push(`${c.pendentes} ${c.pendentes === 1 ? "solicitação pendente" : "solicitações pendentes"}`);
            if (confirmados > 0) resumo.push(`${confirmados} ${confirmados === 1 ? "passageiro confirmado" : "passageiros confirmados"}`);
            if (resumo.length === 0) resumo.push("Nenhuma solicitação ainda");
            return (
              <div key={c.id} className="cartao">
                <div className="cartao-topo">
                  <p className="hora">{dataEHora(c.saida_em)}</p>
                  {c.status === "ABERTA" && <Chip>{textoVagas(c.vagas_disponiveis)}</Chip>}
                  {c.status === "LOTADA" && <Chip tipo="amarelo">Lotada</Chip>}
                  {c.status === "CANCELADA" && <Chip tipo="vermelho">Cancelada</Chip>}
                  {c.status === "CONCLUIDA" && <Chip tipo="cinza">Concluída</Chip>}
                </div>
                <p className="rota">{c.origem}  →  {c.destino}</p>
                <p className="detalhe">{resumo.join(" · ")}</p>
                {ativa && <Link className="botao botao-contorno" to={`/carona/${c.id}/solicitacoes`}>Ver solicitações</Link>}
                {ativa && (
                  <button className="botao botao-perigo" onClick={() => cancelar("Cancelar esta carona? Todos os pedidos serão cancelados.", `/caronas/${c.id}/cancelar`)}>
                    Cancelar carona
                  </button>
                )}
              </div>
            );
          })}
        </>
      )}

      {!carregando && aba === "solicitadas" && (
        <>
          {solicitadas.length === 0 && <p className="vazio">Você ainda não solicitou nenhuma carona</p>}
          {solicitadas.map((s) => {
            const pedidoAtivo = s.solicitacao_status === "PENDENTE" || s.solicitacao_status === "CONFIRMADA";
            return (
              <div key={s.solicitacao_id} className="cartao">
                <div className="cartao-topo">
                  <p className="hora">{dataEHora(s.saida_em)}</p>
                  <ChipStatus status={s.solicitacao_status} />
                </div>
                <p className="rota">{s.origem}  →  {s.destino}</p>
                <p className="detalhe">Motorista: {nomeAbreviado(s.motorista_nome)}</p>
                <p className="detalhe">
                  Veículo: {s.veiculo_modelo}, {s.veiculo_cor.toLowerCase()}
                  {s.veiculo_placa && <> · Placa <strong>{placaParaTela(s.veiculo_placa)}</strong></>}
                </p>
                {s.telefone_motorista && <p className="detalhe">Telefone: {s.telefone_motorista}</p>}
                <Link className="botao botao-contorno" to={`/carona/${s.carona_id}`}>Ver carona</Link>
                {pedidoAtivo && (
                  <button className="botao botao-perigo" onClick={() => cancelar("Cancelar a sua solicitação?", `/solicitacoes/${s.solicitacao_id}/cancelar`)}>
                    Cancelar solicitação
                  </button>
                )}
              </div>
            );
          })}
        </>
      )}
    </Tela>
  );
}
