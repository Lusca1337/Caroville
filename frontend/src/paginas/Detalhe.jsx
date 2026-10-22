import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import Tela from "../componentes/Tela.jsx";
import { Chip, ChipStatus } from "../componentes/Campos.jsx";
import { dataEHora, nomeAbreviado, placaParaTela, textoVagas } from "../util";

// Tela 04 - Detalhe da carona (US03, RF08 e RF09)
export default function Detalhe() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [carona, setCarona] = useState(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  function carregar() {
    api.get(`/caronas/${id}`).then(setCarona).catch((e) => setErro(e.message));
  }
  useEffect(carregar, [id]);

  async function solicitar() {
    setErro("");
    setAviso("");
    try {
      const r = await api.post(`/caronas/${id}/solicitacoes`);
      setAviso(r.mensagem);
      carregar();
    } catch (e) {
      setErro(e.message);
    }
  }

  async function cancelarPedido() {
    if (!window.confirm("Cancelar a sua solicitação?")) return;
    setErro("");
    setAviso("");
    try {
      const r = await api.post(`/solicitacoes/${carona.minha_solicitacao_id}/cancelar`);
      setAviso(r.mensagem);
      carregar();
    } catch (e) {
      setErro(e.message);
    }
  }

  if (!carona) {
    return (
      <Tela titulo="Detalhes da carona">
        {erro ? <p className="erro">{erro}</p> : <p className="vazio">Carregando...</p>}
        <button className="botao botao-contorno" onClick={() => navigate(-1)}>Voltar</button>
      </Tela>
    );
  }

  const ativa = carona.status === "ABERTA";
  const pedido = carona.minha_solicitacao_status; // PENDENTE, CONFIRMADA, ... ou vazio
  const pedidoAtivo = pedido === "PENDENTE" || pedido === "CONFIRMADA";

  return (
    <Tela titulo="Detalhes da carona">
      <div className="cartao cartao-grande">
        <p className="hora-grande">{dataEHora(carona.saida_em)}</p>
        <p className="rota rota-grande">{carona.origem}  →  {carona.destino}</p>
        {carona.ponto_encontro && <p className="detalhe detalhe-grande">Ponto de encontro: {carona.ponto_encontro}</p>}
        <p className="detalhe detalhe-grande">Motorista: {nomeAbreviado(carona.motorista_nome)}</p>
        <p className="detalhe detalhe-grande">
          Veículo: {carona.veiculo_modelo}, {carona.veiculo_cor.toLowerCase()}
        </p>
        {carona.veiculo_placa ? (
          <p className="detalhe detalhe-grande">Placa: <strong>{placaParaTela(carona.veiculo_placa)}</strong></p>
        ) : (
          <p className="detalhe">A placa do carro aparece aqui depois que o motorista aceitar o seu pedido.</p>
        )}
        {carona.observacoes && <p className="detalhe detalhe-grande">Observações: {carona.observacoes}</p>}
        {carona.telefone_motorista && (
          <p className="detalhe detalhe-grande">Telefone do motorista: {carona.telefone_motorista}</p>
        )}
        {carona.status === "ABERTA" && <Chip solto>{textoVagas(carona.vagas_disponiveis)} restantes</Chip>}
        {carona.status === "LOTADA" && <Chip tipo="amarelo" solto>Lotada</Chip>}
        {carona.status === "CANCELADA" && <Chip tipo="vermelho" solto>Carona cancelada</Chip>}
        {carona.status === "CONCLUIDA" && <Chip tipo="cinza" solto>Carona concluída</Chip>}
      </div>

      {pedido && <p className="resumo">Sua solicitação: <ChipStatus status={pedido} /></p>}
      {erro && <p className="erro">{erro}</p>}
      {aviso && <p className="sucesso">{aviso}</p>}
      {carona.sou_motorista && <p className="resumo">Esta é a sua carona, então não dá para solicitar vaga nela.</p>}
      {!carona.sou_motorista && !pedidoAtivo && !ativa && (
        <p className="resumo">Esta carona não está aceitando solicitações.</p>
      )}

      {carona.sou_motorista ? (
        <Link className="botao" to={`/carona/${id}/solicitacoes`}>Ver solicitações</Link>
      ) : pedidoAtivo ? (
        <button className="botao botao-perigo" onClick={cancelarPedido}>Cancelar solicitação</button>
      ) : (
        <button className="botao" onClick={solicitar} disabled={!ativa}>Solicitar carona</button>
      )}
      <button className="botao botao-contorno" onClick={() => navigate(-1)}>Voltar</button>
    </Tela>
  );
}
