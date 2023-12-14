from typing import Optional, Dict, List
from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Rule(Base):
    __tablename__ = "rules"

    id: int = Column(Integer, autoincrement=True)
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
    scope: str
    where: str
    description: Optional[str]
    receivers: List[str]
    output: str
    labels: Dict[str, str]
    chain: Optional[str] = "ethereum"


class Receiver(Base):
    __tablename__ = "receivers"

    id: int = Column(Integer, autoincrement=True)
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
    block_timestamp = Column(DateTime, primary_key=True)
    block_number: int = Column(Integer, index=True)
    hash: str = Column(String, primary_key=True)
    rule_id: str = Column(String, index=True, primary_key=True)
    chain: Optional[str] = Column(String, default="ethereum")
    scope: str = Column(String)
    output: str = Column(String)
    labels: Dict[str, str] = Column(JSONB, nullable=True)
    created_at: str = Column(DateTime, server_default=sa.func.current_timestamp())
    updated_at: str = Column(DateTime, server_default=sa.func.current_timestamp())
    deleted_at: str = Column(DateTime, server_default=None)
