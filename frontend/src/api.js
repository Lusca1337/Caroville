// Comunicação com a API do backend (FastAPI).
const URL_API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// O token do login fica guardado no navegador. Sair = apagar o token.
export const guardarToken = (token) => localStorage.setItem("token", token);
export const lerToken = () => localStorage.getItem("token");
export const apagarToken = () => localStorage.removeItem("token");

async function chamar(metodo, caminho, corpo) {
  const cabecalhos = {};
  const token = lerToken();
  if (token) cabecalhos.Authorization = "Bearer " + token;
  if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";

  let resposta;
  try {
    resposta = await fetch(URL_API + caminho, {
      method: metodo,
      headers: cabecalhos,
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    });
  } catch {
    throw new Error("Não foi possível conectar à API. Ela está rodando?");
  }

  const dados = await resposta.json().catch(() => null);

  if (!resposta.ok) {
    // Sessão expirada: volta para o login (menos na própria tela de login)
    if (resposta.status === 401 && token && caminho !== "/auth/login") {
      apagarToken();
      window.location.href = "/login";
    }
    // A API sempre responde erros como {"detail": "mensagem em português"}
    throw new Error(dados?.detail || "Erro inesperado. Tente novamente.");
  }
  return dados;
}

export const api = {
  get: (caminho) => chamar("GET", caminho),
  post: (caminho, corpo) => chamar("POST", caminho, corpo),
  put: (caminho, corpo) => chamar("PUT", caminho, corpo),
};

// O link de confirmação de e-mail (simulado) vem pronto da API no cadastro
export async function confirmarEmail(link) {
  const resposta = await fetch(link);
  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) throw new Error(dados?.detail || "Link inválido ou expirado");
  return dados;
}
