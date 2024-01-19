from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Rule(Base):
    __tablename__ = "rules"

    name: str = Column(String, primary_key=True)
    scope: str = Column(String, default="block")
    where: str = Column(String, name="_where", index=True)
    description: Optional[str] = Column(String, nullable=True)
    receivers: List[str] = Column(ARRAY(String))
    output: str = Column(String, nullable=True)
    labels: Dict[str, str] = Column(JSONB, nullable=True)
    chain: Optional[str] = Column(String, default="ethereum")
    created_at: str = Column(DateTime, server_default=sa.func.current_timestamp())
    updated_at: str = Column(DateTime, server_default=sa.func.current_timestamp())


class IRule(BaseModel):
    name: str
    scope: Optional[str] = "block"
    where: str
    description: Optional[str]
    receivers: List[str]
    output: Optional[str]
    labels: Optional[Dict[str, str]]
    chain: Optional[str] = "ethereum"


class Receiver(Base):
    __tablename__ = "receivers"

    name: str = Column(String, primary_key=True)
    receiver: str = Column(String)
    init_args: Optional[Dict[str, str]] = Column(JSONB)
    created_at: str = Column(DateTime, server_default=sa.func.current_timestamp())
    updated_at: str = Column(DateTime, server_default=sa.func.current_timestamp())


class IReceiver(BaseModel):
    name: str
    receiver: str
    init_args: Optional[Dict[str, str]]


class Alert(Base):
    __tablename__ = "alerts"

    id: str = Column(String, index=True)
    block_timestamp: int = Column(DateTime, primary_key=True)
    block_number: int = Column(Integer, index=True)
    hash: str = Column(String, primary_key=True)
    rule_name: str = Column(String, index=True, primary_key=True)
    chain: Optional[str] = Column(String, default="ethereum")
    scope: str = Column(String)
    output: str = Column(String)
    labels: Dict[str, str] = Column(JSONB, nullable=True)
    created_at: int = Column(DateTime, server_default=sa.func.current_timestamp())
    updated_at: int = Column(DateTime, server_default=sa.func.current_timestamp())
    deleted_at: Optional[int] = Column(DateTime, server_default=None)
    

class AlertResponse(BaseModel):
    id: str
    block_timestamp: datetime
    block_number: int
    hash: str
    rule_name: str
    chain: str
    scope: str
    output: str
    labels: Dict[str, str]
    
    class Config: 
        json_encoders = {
            datetime: lambda v: int(v.timestamp()),
        }


INIT_SQL = """
CREATE SCHEMA IF NOT EXISTS {schema};

CREATE TABLE IF NOT EXISTS {schema}.rules (
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
CREATE INDEX IF NOT EXISTS webe3_rules_chain_idx ON {schema}.rules (chain);
CREATE INDEX IF NOT EXISTS webe3_rules_where_idx ON {schema}.rules (_where);

CREATE TABLE IF NOT EXISTS {schema}.receivers (
    id              SERIAL,
    name            TEXT NOT NULL,
    receiver        TEXT NOT NULL,
    init_args       JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS {schema}.alerts (
    id              TEXT,
    block_timestamp TIMESTAMP NOT NULL,
    block_number    BIGINT NOT NULL,
    hash            TEXT NOT NULL,
    rule_name         TEXT NOT NULL,
    scope           TEXT NOT NULL,
    chain           TEXT NOT NULL DEFAULT 'ethereum',
    output          TEXT,
    labels          JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP DEFAULT NULL,

    PRIMARY KEY (block_timestamp, hash, rule_name)
);

CREATE INDEX IF NOT EXISTS {schema}_alerts_id_idx ON {schema}.alerts(id);
"""
