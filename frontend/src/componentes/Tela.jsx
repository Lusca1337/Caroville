import { Link } from "react-router-dom";

// Ícones do menu: desenhos simples em SVG (traço), que herdam a cor do texto do item
const props = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" };

const IconeBuscar = (  // lupa
  <svg {...props}>
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.5" y2="16.5" />
  </svg>
);
const IconeOferecer = (  // carro
  <svg {...props}>
    <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
    <circle cx="7" cy="17" r="2" />
    <path d="M9 17h6" />
    <circle cx="17" cy="17" r="2" />
  </svg>
);
const IconeMinhas = (  // lista
  <svg {...props}>
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" />
    <line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
);
const IconePerfil = (  // pessoa
  <svg {...props}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const ABAS = [
  { id: "buscar", texto: "Buscar", para: "/", icone: IconeBuscar },
  { id: "oferecer", texto: "Oferecer", para: "/oferecer", icone: IconeOferecer },
  { id: "minhas", texto: "Minhas", para: "/minhas", icone: IconeMinhas },
  { id: "perfil", texto: "Perfil", para: "/perfil", icone: IconePerfil },
];

// Estrutura comum das telas: cabeçalho verde, conteúdo e (opcionalmente) o menu de baixo.
// "menu" diz qual aba fica destacada; sem ele, a tela não mostra o menu.
export default function Tela({ titulo, menu, children }) {
  return (
    <div className="tela">
      <header className="cabecalho">
        <h1>{titulo}</h1>
      </header>
      <main className="conteudo">{children}</main>
      {menu && (
        <nav className="menu">
          {ABAS.map((aba) => (
            <Link
              key={aba.id}
              to={aba.para}
              className={"menu-item" + (aba.id === menu ? " ativo" : "")}
            >
              <span className="menu-icone">{aba.icone}</span>
              <span>{aba.texto}</span>
            </Link>
          ))}
        </nav>
      )}
    </div>
  );
}
