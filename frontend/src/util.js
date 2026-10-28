// Funções pequenas de formatação usadas em várias telas.
const DIAS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const dois = (n) => String(n).padStart(2, "0");

// "2026-10-20T18:00:00" -> "18:00"
export function horaCurta(iso) {
  const d = new Date(iso);
  return `${dois(d.getHours())}:${dois(d.getMinutes())}`;
}

// "2026-10-20T18:00:00" -> "Hoje · 18:00", "Amanhã · 18:00", "Seg · 18:00" ou "20/10 · 18:00"
export function dataEHora(iso) {
  const d = new Date(iso);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const dia = new Date(d);
  dia.setHours(0, 0, 0, 0);
  const diferenca = Math.round((dia - hoje) / 86400000);

  let rotulo;
  if (diferenca === 0) rotulo = "Hoje";
  else if (diferenca === 1) rotulo = "Amanhã";
  else if (diferenca > 1 && diferenca < 7) rotulo = DIAS[d.getDay()];
  else rotulo = `${dois(d.getDate())}/${dois(d.getMonth() + 1)}`;
  return `${rotulo} · ${horaCurta(iso)}`;
}

// "Lucas Felipe" -> "Lucas F."
export function nomeAbreviado(nome) {
  const partes = (nome || "").trim().split(/\s+/);
  if (partes.length < 2) return partes[0] || "";
  return `${partes[0]} ${partes[partes.length - 1][0]}.`;
}

export const textoVagas = (n) => (n === 1 ? "1 vaga" : `${n} vagas`);

// Data e hora no formato do campo datetime-local: "2026-10-20T18:00"
function paraCampo(d) {
  return `${d.getFullYear()}-${dois(d.getMonth() + 1)}-${dois(d.getDate())}T${dois(d.getHours())}:${dois(d.getMinutes())}`;
}

// Agora (ou daqui a X horas). Serve como valor mínimo dos campos de data: nada de data passada.
export function agoraParaCampo(horasAFrente = 0) {
  return paraCampo(new Date(Date.now() + horasAFrente * 3600000));
}

// Data de hoje no formato do campo date: "2026-10-20"
export const hojeParaCampo = () => agoraParaCampo().slice(0, 10);

// Valor inicial dos campos de data e hora: daqui a 2 horas, em hora cheia (a regra RN04 pede 1 hora de antecedência)
export function horarioPadrao() {
  const d = new Date(Date.now() + 2 * 3600000);
  d.setMinutes(0, 0, 0);
  return paraCampo(d);
}

// Máscara do telefone enquanto a pessoa digita: (11) 9 9999-9999 (qualquer DDD e qualquer número)
// Só aceita números e para nos 11 dígitos (DDD + número com 9 dígitos).
export function mascaraTelefone(texto) {
  const d = (texto || "").replace(/\D/g, "").slice(0, 11);
  if (d.length === 0) return "";
  let r = "(" + d.slice(0, 2);
  if (d.length > 2) r += ") " + d.slice(2, 3);
  if (d.length > 3) r += " " + d.slice(3, 7);
  if (d.length > 7) r += "-" + d.slice(7, 11);
  return r;
}

// DDDs que existem no Brasil (a mesma lista do backend)
const DDDS = new Set([
  11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38,
  41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69,
  71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99,
]);

// Confere o telefone no formato (DDD) 9 9999-9999 e devolve a mensagem do problema ("" se estiver certo).
// Aceita DDD de qualquer estado e qualquer número, desde que siga a formatação.
export function erroTelefone(t) {
  if (!/^\(\d\d\) \d \d{4}-\d{4}$/.test(t)) return "Telefone incompleto. Use DDD + número, ex.: (11) 9 9999-9999";
  if (!DDDS.has(Number(t.slice(1, 3)))) return "DDD inválido";
  return "";
}

// Placa enquanto a pessoa digita: só letras e números, em maiúsculas, até 7 caracteres
export const mascaraPlaca = (texto) => (texto || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 7);

// Placa antiga (ABC1234) ou Mercosul (ABC1D23)
export const placaValida = (p) => /^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$/.test(p);
export const MSG_PLACA = "Placa inválida. Use ABC-1234 ou ABC1D23";

// Placa que veio do banco: "ABC1234" -> "ABC-1234" (a Mercosul fica como está)
export function placaParaTela(p) {
  return /^[A-Z]{3}\d{4}$/.test(p || "") ? `${p.slice(0, 3)}-${p.slice(3)}` : p || "";
}

// Telefone que veio do banco: se tiver 11 números, mostra com a máscara; senão, deixa como está
export function telefoneParaTela(t) {
  return (t || "").replace(/\D/g, "").length === 11 ? mascaraTelefone(t) : t || "";
}
