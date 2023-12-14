CREATE SCHEMA IF NOT EXISTS web3;

CREATE TABLE IF NOT EXISTS web3.rules (
    id              SERIAL,
    name            TEXT NOT NULL,
    scope           TEXT NOT NULL DEFAULT 'block',
    _where          TEXT NOT NULL,
    description     TEXT,
    receivers       TEXT[] NOT NULL,
    output          TEXT,
    labels          JSONB,
    chain           TEXT NOT NULL DEFAULT 'ethereum',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (name)
);
CREATE INDEX IF NOT EXISTS webe3_rules_chain_idx ON web3.rules (chain);
CREATE INDEX IF NOT EXISTS webe3_rules_where_idx ON web3.rules (_where);

CREATE TABLE IF NOT EXISTS web3.receivers (
    id              SERIAL,
    name            TEXT NOT NULL,
    receiver        TEXT NOT NULL,
    init_args       JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS web3.alerts (
    id              TEXT,
    block_timestamp TIMESTAMP NOT NULL,
    block_number    BIGINT NOT NULL,
    hash            TEXT NOT NULL,
    rule_id         TEXT NOT NULL,
    scope           TEXT NOT NULL,
    chain           TEXT NOT NULL DEFAULT 'ethereum',
    output          TEXT,
    labels          JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP DEFAULT NULL,

    PRIMARY KEY (block_timestamp, hash, rule_id)
);

CREATE INDEX IF NOT EXISTS web3_alerts_id_idx ON web3.alerts(id);
