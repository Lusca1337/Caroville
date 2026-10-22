# Caroville - Frontend

React + Vite. Precisa da API (pasta `backend`) rodando em `http://localhost:8000`.

## Como rodar

1. Instale o **Node.js** (versão 18 ou mais nova): https://nodejs.org
2. Na pasta `frontend`:
   ```
   npm install
   npm run dev
   ```
3. Abra http://localhost:5173

O backend só aceita chamadas vindas da porta **5173**. Se ela estiver ocupada, o Vite mostra um erro em vez de trocar de porta; feche o que está usando a porta e rode de novo.

Usuários de teste (senha `senha1234`): `lucas@univille.br` (tem veículo), `maria@univille.br` e `joao@univille.br`.

## Estrutura

```
src/
├── main.jsx          ponto de entrada
├── App.jsx           rotas (quais telas exigem login)
├── api.js            chamadas à API e guarda do token
├── util.js           formatação de datas, nomes e vagas
├── estilos.css       cores e medidas do Figma
├── componentes/      Tela (cabeçalho + menu) e peças pequenas
└── paginas/          uma por tela do Figma
```

| Tela do Figma | Arquivo | Endereço |
|---------------|---------|----------|
| 01 Login | `Login.jsx` | `/login` |
| 02 Cadastro | `Cadastro.jsx` | `/cadastro` |
| 03 Buscar caronas | `Buscar.jsx` | `/` |
| 04 Detalhe da carona | `Detalhe.jsx` | `/carona/:id` |
| 05 Oferecer carona | `Oferecer.jsx` | `/oferecer` |
| 06 Minhas caronas | `Minhas.jsx` | `/minhas` |
| 07 Solicitações recebidas | `Solicitacoes.jsx` | `/carona/:id/solicitacoes` |
| 08 Perfil | `Perfil.jsx` | `/perfil` |
