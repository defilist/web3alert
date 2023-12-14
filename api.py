#!/usr/bin/env python

import os
import logging
import uvicorn
from fastapi import status
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import typer
from typer import Typer

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
import rule_engine

from hack.model import Alert, Rule, Receiver, Base, IRule, IReceiver

logging.basicConfig(
    format="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.INFO
)


app = FastAPI()
cli = Typer()

engine = None
SessionLocal = None


def create_db_engine(database_url: str, schema_name="web3", auto_create: bool = False):
    global engine, SessionLocal
    connect_args = {"options": f"-c search_path={schema_name}"}
    engine = sa.create_engine(
        database_url,
        connect_args=connect_args,
        echo=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if auto_create:
        if not engine.dialect.has_schema(engine, schema_name):
            engine.execute(sa.schema.CreateSchema(schema_name))
        Base.metadata.create_all(bind=engine)


def get_db():
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = get_db


@app.post("/rules")
async def create_rule(
    irule: IRule,
    db: Session = Depends(get_db),
):
    rule = Rule(**irule.model_dump())
    try:
        context = rule_engine.Context(default_value=None)
        rule_engine.Rule(rule.where, context=context)
    except Exception as e:
        logging.error(f"Error creating rule({rule}): {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": f"Error creating rule: {e}"}),
        )

    if len(rule.output) == 0 and len(rule.labels) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": "No output or labels specified"}),
        )
    if len(rule.receivers or []) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": "No receivers specified"}),
        )

    exists = db.query(Receiver).filter(Receiver.name.in_(rule.receivers)).all()  # type: ignore
    if len(exists) != len(rule.receivers):
        unknown = set(rule.receivers) - set([r.name for r in exists])
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": f"Invalid receivers, unknown: {unknown}"}),
        )

    # finally commit it
    db.add(rule)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder({"msg": "Rule created"}),
    )


@app.get("/rules/")
async def get_rules(db: Session = Depends(get_db)):
    rule = db.query(Rule).all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(rule),
    )


@app.get("/rules/{name}")
async def get_rule(name: str, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.name == name).first()  # type: ignore
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(rule),
    )


@app.post("/receivers")
async def create_receiver(
    ireceiver: IReceiver,
    db: Session = Depends(get_db),
):
    receiver = Receiver(**ireceiver.model_dump())
    db.add(receiver)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder({"msg": "Receiver created"}),
    )


@app.get("/receivers/")
async def get_receivers(db: Session = Depends(get_db)):
    receiver = db.query(Receiver).all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(receiver),
    )


@app.get("/receivers/{name}")
async def get_receiver(name: str, db: Session = Depends(get_db)):
    receiver = db.query(Receiver).filter(Receiver.name == name).first()  # type: ignore
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(receiver),
    )


@app.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(alerts),
    )


@cli.command()
def start_server(
    database_url: str = os.getenv("DATABASE_URL"),
    port: int = 8000,
    auto_create_db: bool = False,
):
    create_db_engine(database_url, auto_create=auto_create_db)
    typer.echo("Running FastAPI server...")
    typer.echo(f"Database URL: {database_url}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    cli()
