-- Caroville - estrutura do banco de dados (PostgreSQL)
-- Segue o DER do README. Para recriar do zero, rode este arquivo inteiro.

DROP TABLE IF EXISTS solicitacao CASCADE;
DROP TABLE IF EXISTS carona CASCADE;
DROP TABLE IF EXISTS local CASCADE;
DROP TABLE IF EXISTS veiculo CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

CREATE TABLE usuario (
    id               SERIAL PRIMARY KEY,
    nome             VARCHAR(100) NOT NULL,
    email            VARCHAR(150) NOT NULL UNIQUE,
    senha_hash       VARCHAR(100) NOT NULL,
    curso            VARCHAR(100) NOT NULL,
    telefone         VARCHAR(20)  NOT NULL,
    email_verificado BOOLEAN      NOT NULL DEFAULT FALSE,
    criado_em        TIMESTAMP    NOT NULL DEFAULT now(),
    -- RN01: só e-mail institucional
    CONSTRAINT usuario_email_institucional CHECK (email LIKE '%@univille.br')
);

CREATE TABLE veiculo (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER     NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    modelo     VARCHAR(60) NOT NULL,
    cor        VARCHAR(30) NOT NULL,
    lugares    INTEGER     NOT NULL,
    CONSTRAINT veiculo_lugares CHECK (lugares BETWEEN 2 AND 8)
);

CREATE TABLE local (
    id   SERIAL PRIMARY KEY,
    nome VARCHAR(80) NOT NULL UNIQUE,
    tipo VARCHAR(10) NOT NULL,
    CONSTRAINT local_tipo CHECK (tipo IN ('BAIRRO', 'CAMPUS'))
);

CREATE TABLE carona (
    id                SERIAL PRIMARY KEY,
    motorista_id      INTEGER      NOT NULL REFERENCES usuario(id),
    veiculo_id        INTEGER      NOT NULL REFERENCES veiculo(id),
    origem_id         INTEGER      NOT NULL REFERENCES local(id),
    destino_id        INTEGER      NOT NULL REFERENCES local(id),
    saida_em          TIMESTAMP    NOT NULL,
    vagas_total       INTEGER      NOT NULL,
    vagas_disponiveis INTEGER      NOT NULL,
    ponto_encontro    VARCHAR(120),
    observacoes       VARCHAR(255),
    status            VARCHAR(10)  NOT NULL DEFAULT 'ABERTA',
    criado_em         TIMESTAMP    NOT NULL DEFAULT now(),
    -- RN03: de 1 a 4 vagas
    CONSTRAINT carona_vagas_total CHECK (vagas_total BETWEEN 1 AND 4),
    CONSTRAINT carona_vagas_disponiveis CHECK (vagas_disponiveis BETWEEN 0 AND vagas_total),
    CONSTRAINT carona_origem_destino CHECK (origem_id <> destino_id),
    CONSTRAINT carona_status CHECK (status IN ('ABERTA', 'LOTADA', 'CANCELADA', 'CONCLUIDA'))
);

CREATE TABLE solicitacao (
    id            SERIAL PRIMARY KEY,
    carona_id     INTEGER     NOT NULL REFERENCES carona(id) ON DELETE CASCADE,
    passageiro_id INTEGER     NOT NULL REFERENCES usuario(id),
    status        VARCHAR(10) NOT NULL DEFAULT 'PENDENTE',
    criado_em     TIMESTAMP   NOT NULL DEFAULT now(),
    respondido_em TIMESTAMP,
    CONSTRAINT solicitacao_status CHECK (
        status IN ('PENDENTE', 'CONFIRMADA', 'RECUSADA', 'CANCELADA', 'EXPIRADA')
    )
);

-- RN06: um passageiro só pode ter uma solicitação ativa por carona
CREATE UNIQUE INDEX solicitacao_ativa_unica
    ON solicitacao (carona_id, passageiro_id)
    WHERE status IN ('PENDENTE', 'CONFIRMADA');

-- Índice para a busca de caronas (RF07)
CREATE INDEX carona_busca ON carona (origem_id, destino_id, saida_em);
