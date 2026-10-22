// Peças pequenas reutilizadas nas telas.

// Rótulo + campo (input ou select)
export function Campo({ rotulo, children }) {
  return (
    <label className="campo">
      <span className="rotulo">{rotulo}</span>
      {children}
    </label>
  );
}

// Etiqueta arredondada: tipo = verde | amarelo | cinza | vermelho
export function Chip({ tipo = "verde", solto = false, children }) {
  const classes = `chip chip-${tipo}` + (solto ? " chip-solto" : "");
  return <span className={classes}>{children}</span>;
}

// Status de solicitação -> texto e cor
const STATUS = {
  PENDENTE: ["Pendente", "amarelo"],
  CONFIRMADA: ["Confirmada", "verde"],
  RECUSADA: ["Recusada", "vermelho"],
  CANCELADA: ["Cancelada", "cinza"],
  EXPIRADA: ["Expirada", "cinza"],
};

export function ChipStatus({ status, solto }) {
  const [texto, tipo] = STATUS[status] || [status, "cinza"];
  return <Chip tipo={tipo} solto={solto}>{texto}</Chip>;
}
