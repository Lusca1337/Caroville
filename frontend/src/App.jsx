import { Navigate, Route, Routes } from "react-router-dom";
import { lerToken } from "./api";
import Login from "./paginas/Login.jsx";
import Cadastro from "./paginas/Cadastro.jsx";
import Buscar from "./paginas/Buscar.jsx";
import Detalhe from "./paginas/Detalhe.jsx";
import Oferecer from "./paginas/Oferecer.jsx";
import Minhas from "./paginas/Minhas.jsx";
import Solicitacoes from "./paginas/Solicitacoes.jsx";
import Perfil from "./paginas/Perfil.jsx";

// Telas que exigem login: sem token, volta para o login
function Protegida({ children }) {
  return lerToken() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <div className="celular">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/" element={<Protegida><Buscar /></Protegida>} />
        <Route path="/carona/:id" element={<Protegida><Detalhe /></Protegida>} />
        <Route path="/carona/:id/solicitacoes" element={<Protegida><Solicitacoes /></Protegida>} />
        <Route path="/oferecer" element={<Protegida><Oferecer /></Protegida>} />
        <Route path="/minhas" element={<Protegida><Minhas /></Protegida>} />
        <Route path="/perfil" element={<Protegida><Perfil /></Protegida>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
