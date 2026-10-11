# 1. Requisitos Funcionais, Histórias de Usuário e Regras de Negócio

## 1.1 Requisitos Funcionais (RF)

| ID | Requisito | História |
|----|-----------|----------|
| RF01 | O sistema deve permitir cadastro com nome, e-mail institucional, curso, telefone e senha. | US01 |
| RF02 | O sistema deve confirmar o e-mail por link enviado ao endereço cadastrado. | US01 |
| RF03 | O sistema deve permitir login e logout. | US01 |
| RF04 | O usuário deve poder editar nome, curso e telefone. | US06 |
| RF05 | O usuário deve poder cadastrar um veículo (modelo, cor, número de lugares). | US06 |
| RF06 | O motorista deve poder publicar uma carona com saída, destino, data/hora, vagas e observações. | US02 |
| RF07 | O sistema deve buscar caronas por saída, destino e horário (janela de ±30 min). | US03 |
| RF08 | O sistema deve exibir os detalhes de uma carona (motorista, veículo, ponto de encontro, vagas). | US03 |
| RF09 | O passageiro deve poder solicitar uma vaga em uma carona. | US03 |
| RF10 | O motorista deve poder aceitar ou recusar solicitações pendentes. | US04 |
| RF11 | O sistema deve atualizar as vagas disponíveis a cada aceite ou cancelamento. | US04, US05 |
| RF12 | O passageiro deve poder cancelar uma solicitação. | US05 |
| RF13 | O motorista deve poder cancelar uma carona. | US05 |
| RF14 | O usuário deve listar suas caronas oferecidas e solicitadas, com status. | US05 |
| RF15 | O sistema deve enviar e-mail quando uma solicitação for aceita, recusada ou cancelada. | US04, US05 |
| RF16 | O sistema deve liberar o telefone do motorista e do passageiro somente após o aceite. | US04 |

## 1.2 Histórias de Usuário e Critérios de Aceite

### US01 - Cadastro e login
**Como** estudante, **quero** criar uma conta com meu e-mail institucional **para** usar a plataforma com segurança.
Telas: 01 Login, 02 Cadastro. RFs: RF01, RF02, RF03.

```gherkin
Cenário: Cadastro com e-mail institucional válido
  Dado que estou na tela de cadastro
  Quando preencho todos os campos com um e-mail terminado em @univille.br e envio
  Então a conta é criada
  E recebo um e-mail com o link de confirmação

Cenário: Cadastro com e-mail não institucional
  Dado que estou na tela de cadastro
  Quando informo um e-mail de outro domínio (ex.: @gmail.com)
  Então vejo a mensagem "Use seu e-mail institucional"
  E a conta não é criada

Cenário: Login sem e-mail confirmado
  Dado que criei a conta mas não confirmei o e-mail
  Quando tento fazer login
  Então o acesso é negado com a mensagem "Confirme seu e-mail"
```

### US02 - Oferecer carona
**Como** motorista, **quero** publicar uma carona **para** dividir meu trajeto com colegas.
Tela: 05 Oferecer carona. RFs: RF06. RNs: RN02, RN03, RN04.

```gherkin
Cenário: Publicar carona válida
  Dado que estou logado e tenho um veículo cadastrado
  Quando informo saída, destino, horário futuro e 3 vagas e clico em "Publicar carona"
  Então a carona aparece em "Minhas caronas > Oferecidas" com status "Aberta"

Cenário: Publicar sem veículo
  Dado que estou logado e não tenho veículo cadastrado
  Quando tento publicar uma carona
  Então sou orientado a cadastrar um veículo no perfil

Cenário: Horário no passado
  Dado que estou no formulário de oferta
  Quando informo um horário com menos de 1 hora de antecedência
  Então vejo a mensagem "Informe um horário futuro" e a carona não é criada
```

### US03 - Buscar e solicitar carona
**Como** passageiro, **quero** encontrar caronas com trajeto e horário parecidos com os meus **para** chegar à faculdade.
Telas: 03 Buscar caronas, 04 Detalhe da carona. RFs: RF07, RF08, RF09. RNs: RN05, RN06, RN12.

```gherkin
Cenário: Buscar caronas compatíveis
  Dado que existem caronas abertas com saída "Costa e Silva" às 18:00
  Quando busco saída "Costa e Silva", destino "Campus Univille" e horário 18:15
  Então vejo a carona das 18:00 na lista de resultados

Cenário: Nenhum resultado
  Dado que não há caronas na janela de ±30 min
  Quando realizo a busca
  Então vejo "Nenhuma carona encontrada"

Cenário: Solicitar vaga
  Dado que estou no detalhe de uma carona com vagas disponíveis
  Quando clico em "Solicitar carona"
  Então a solicitação é criada com status "Pendente"
  E o motorista é notificado

Cenário: Solicitar a própria carona
  Dado que sou o motorista da carona
  Quando tento solicitá-la
  Então a ação é bloqueada
```

### US04 - Gerenciar solicitações
**Como** motorista, **quero** aceitar ou recusar pedidos **para** controlar quem viaja comigo.
Tela: 07 Solicitações recebidas. RFs: RF10, RF11, RF15, RF16. RNs: RN07, RN10.

```gherkin
Cenário: Aceitar solicitação
  Dado que tenho uma solicitação pendente e vagas disponíveis
  Quando clico em "Aceitar"
  Então a solicitação passa para "Confirmada"
  E as vagas disponíveis diminuem em 1
  E o passageiro recebe e-mail com meu telefone

Cenário: Aceitar sem vagas
  Dado que a carona não tem vagas disponíveis
  Quando tento aceitar outra solicitação
  Então a ação é bloqueada com a mensagem "Carona lotada"

Cenário: Recusar solicitação
  Dado que tenho uma solicitação pendente
  Quando clico em "Recusar"
  Então a solicitação passa para "Recusada"
  E o passageiro é notificado
```

### US05 - Acompanhar e cancelar caronas
**Como** usuário, **quero** ver o status das minhas caronas e cancelar quando necessário **para** avisar os envolvidos.
Tela: 06 Minhas caronas. RFs: RF11, RF12, RF13, RF14, RF15. RNs: RN08, RN09.

```gherkin
Cenário: Listar minhas caronas
  Dado que estou logado
  Quando abro "Minhas caronas"
  Então vejo as abas "Oferecidas" e "Solicitadas" com o status de cada item

Cenário: Cancelar com antecedência suficiente
  Dado que faltam mais de 2 horas para a saída
  Quando cancelo minha carona ou solicitação
  Então o status muda para "Cancelada"
  E os envolvidos são notificados por e-mail

Cenário: Cancelar fora do prazo
  Dado que faltam menos de 2 horas para a saída
  Quando tento cancelar
  Então a ação é bloqueada com a mensagem "Prazo de cancelamento encerrado"

Cenário: Motorista cancela carona com passageiros
  Dado que a carona tem passageiros confirmados
  Quando o motorista cancela a carona
  Então todas as solicitações passam para "Cancelada"
  E cada passageiro recebe e-mail
```

### US06 - Perfil e veículo
**Como** usuário, **quero** manter meus dados e meu veículo atualizados **para** que os colegas confiem na carona.
Tela: 08 Perfil. RFs: RF04, RF05. RN: RN03.

```gherkin
Cenário: Atualizar dados
  Dado que estou no perfil
  Quando altero o telefone e clico em "Salvar alterações"
  Então os dados são salvos e exibidos atualizados

Cenário: Cadastrar veículo
  Dado que não tenho veículo
  Quando informo modelo, cor e 4 lugares
  Então o veículo é salvo e posso publicar caronas
```

## 1.3 Regras de Negócio (RN)

| ID | Regra |
|----|-------|
| RN01 | Só são aceitos cadastros com e-mail do domínio institucional (@univille.br). O e-mail é único no sistema. |
| RN02 | Só é possível oferecer carona com pelo menos um veículo cadastrado. |
| RN03 | O número de vagas ofertadas deve ser de 1 até (lugares do veículo - 1), no máximo 6. |
| RN04 | A saída da carona deve ocorrer com pelo menos 1 hora de antecedência da publicação. |
| RN05 | O motorista não pode solicitar vaga na própria carona. |
| RN06 | Cada passageiro pode ter apenas uma solicitação ativa (pendente ou confirmada) por carona. |
| RN07 | Uma solicitação só pode ser aceita se houver vaga; ao aceitar, as vagas disponíveis diminuem em 1. |
| RN08 | Cancelamentos (de carona ou de solicitação) só podem ser feitos até 2 horas antes da saída. |
| RN09 | Ao cancelar uma carona, todas as solicitações pendentes e confirmadas passam a "Cancelada". |
| RN10 | O telefone do motorista e do passageiro só é exibido entre os dois após o aceite. |
| RN11 | Solicitações pendentes de caronas cuja saída já passou mudam automaticamente para "Expirada". |
| RN12 | Um passageiro não pode ter duas caronas confirmadas com saídas a menos de 1 hora uma da outra. |
| RN13 | Caronas com saída no passado e não canceladas passam para "Concluída". |
| RN14 | Locais de saída e destino são escolhidos de uma lista de bairros e campi cadastrados (sem geolocalização no MVP). |
| RN15 | No MVP as caronas são gratuitas: o sistema não processa pagamentos. |

### Status
- **Carona:** Aberta, Lotada, Cancelada, Concluída.
- **Solicitação:** Pendente, Confirmada, Recusada, Cancelada, Expirada.
