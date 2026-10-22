-- Caroville - dados iniciais para teste
-- Rode depois do schema.sql.
-- Todos os usuários de teste usam a senha: senha1234

INSERT INTO local (nome, tipo) VALUES
    ('Campus Univille', 'CAMPUS'),
    ('Costa e Silva',   'BAIRRO'),
    ('Boa Vista',       'BAIRRO'),
    ('Glória',          'BAIRRO'),
    ('Centro',          'BAIRRO'),
    ('Atiradores',      'BAIRRO'),
    ('Aventureiro',     'BAIRRO'),
    ('Itaum',           'BAIRRO');

INSERT INTO usuario (nome, email, senha_hash, curso, telefone, email_verificado) VALUES
    ('Lucas Felipe',  'lucas@univille.br',  '$2b$10$Tkx.97JaKaUCFu92eSSTp.j14BDNXrvnc91zUGSYIWTxA5JVMeM9S', 'Ciência da Computação', '(47) 90000-0001', TRUE),
    ('Maria Souza',   'maria@univille.br',  '$2b$10$Tkx.97JaKaUCFu92eSSTp.j14BDNXrvnc91zUGSYIWTxA5JVMeM9S', 'Engenharia Civil',      '(47) 90000-0002', TRUE),
    ('João Pereira',  'joao@univille.br',   '$2b$10$Tkx.97JaKaUCFu92eSSTp.j14BDNXrvnc91zUGSYIWTxA5JVMeM9S', 'Administração',         '(47) 90000-0003', TRUE);

INSERT INTO veiculo (usuario_id, modelo, cor, placa, lugares) VALUES
    (1, 'Fiat Argo', 'Prata', 'QJB2E45', 5);

-- Datas calculadas a partir de agora, para os dados de teste nunca ficarem no passado
INSERT INTO carona (motorista_id, veiculo_id, origem_id, destino_id, saida_em, vagas_total, vagas_disponiveis, ponto_encontro, observacoes) VALUES
    (1, 1, 2, 1, date_trunc('hour', now()) + interval '1 day 2 hours', 3, 3, 'Praça da Bandeira', 'Saio pontualmente'),
    (1, 1, 3, 1, date_trunc('hour', now()) + interval '2 days 2 hours', 2, 2, NULL, NULL);
