# 2. Requisitos Não Funcionais (RNF)

## Desempenho
| ID | Requisito |
|----|-----------|
| RNF01 | A busca de caronas responde em até 1 segundo, com até 100 usuários ao mesmo tempo. |
| RNF02 | A tela inicial carrega em até 3 segundos no 4G. |

## Disponibilidade
| ID | Requisito |
|----|-----------|
| RNF03 | O sistema fica no ar pelo menos 99% do mês. |
| RNF04 | O banco de dados tem backup automático todo dia. |

## Segurança
| ID | Requisito |
|----|-----------|
| RNF05 | Todo acesso é por HTTPS. |
| RNF06 | As senhas são guardadas criptografadas (bcrypt), nunca em texto puro. |
| RNF07 | Depois de 5 senhas erradas seguidas, o login fica bloqueado por 15 minutos. |
| RNF08 | O telefone de motorista e passageiro só aparece depois que a carona é aceita. |

## Usabilidade
| ID | Requisito |
|----|-----------|
| RNF09 | Publicar uma carona leva no máximo 1 minuto e 2 telas. |
| RNF10 | A interface funciona em telas de 360 px até 1440 px, sem rolagem horizontal. |
