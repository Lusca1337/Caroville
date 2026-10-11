# 2. Requisitos Não Funcionais (RNF)

Condição de "carga normal": até 100 usuários simultâneos e 5.000 caronas ativas no banco.

## Desempenho
| ID | Requisito | Como medir |
|----|-----------|-----------|
| RNF01 | A busca de caronas (RF07) deve responder em menos de 800 ms no percentil 95 sob carga normal. | Teste de carga com k6 |
| RNF02 | Os demais endpoints da API devem responder em menos de 500 ms no percentil 95 sob carga normal. | k6 / logs da API |
| RNF03 | O Largest Contentful Paint da tela inicial deve ser menor que 2,5 s em rede 4G simulada. | Lighthouse |

## Disponibilidade e confiabilidade
| ID | Requisito | Como medir |
|----|-----------|-----------|
| RNF04 | Disponibilidade mensal mínima de 99% (MVP). | Monitor de uptime |
| RNF05 | Backup automático diário do banco, com retenção de 7 dias (RPO de 24 h). | Painel do provedor |
| RNF06 | E-mails de notificação (RF15) enviados em até 60 s após o evento. | Log do serviço de e-mail |

## Segurança
| ID | Requisito | Como medir |
|----|-----------|-----------|
| RNF07 | Todo o tráfego deve usar HTTPS (TLS 1.2 ou superior). | SSL Labs, nota A ou superior |
| RNF08 | Senhas armazenadas com bcrypt (custo mínimo 10); nunca em texto puro. | Revisão de código |
| RNF09 | Tokens JWT de acesso expiram em 1 h; refresh token em 7 dias. | Teste automatizado |
| RNF10 | Bloqueio temporário após 5 tentativas de login falhas em 15 min, por e-mail e por IP. | Teste automatizado |
| RNF11 | Nenhuma vulnerabilidade crítica ou alta no OWASP ZAP (scan baseline) antes da entrega. | Relatório do ZAP |
| RNF12 | Telefone e e-mail só visíveis conforme RN10; exclusão de conta atendida em até 15 dias (LGPD). | Teste manual + procedimento documentado |

## Usabilidade e acessibilidade
| ID | Requisito | Como medir |
|----|-----------|-----------|
| RNF13 | Publicar uma carona em no máximo 2 telas e 60 s. | Teste de usabilidade cronometrado |
| RNF14 | Pelo menos 4 de 5 testadores concluem "buscar e solicitar carona" sem ajuda. | Teste com 5 alunos |
| RNF15 | Contraste de texto mínimo de 4,5:1 (WCAG 2.1 AA). | Lighthouse / Axe |
| RNF16 | Interface responsiva de 360 px a 1440 px de largura, sem rolagem horizontal. | Teste em DevTools |

## Compatibilidade e manutenibilidade
| ID | Requisito | Como medir |
|----|-----------|-----------|
| RNF17 | Suporte às 2 últimas versões de Chrome, Firefox, Safari e Edge. | Teste manual |
| RNF18 | Cobertura de testes automatizados de pelo menos 70% nas regras de negócio do backend. | Relatório de cobertura (Jest) |
| RNF19 | O pipeline de CI deve rodar lint e testes a cada pull request; merge só com pipeline verde. | GitHub Actions |
