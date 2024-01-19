#!/usr/bin/env python

import os
import logging
import uvicorn
from fastapi import status
from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

import typer
from typer import Typer
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
import rule_engine

from hack.model import Alert, Rule, Receiver, IRule, IReceiver, INIT_SQL

logging.basicConfig(
    format="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.INFO
)


app = FastAPI()
app = add_pagination(app)
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
        # if not engine.dialect.has_schema(engine, schema_name):
        #     engine.execute(sa.schema.CreateSchema(schema_name))
        # Base.metadata.create_all(bind=engine)
        init_sql = INIT_SQL.format(schema=schema_name)
        engine.execute(init_sql)


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


@app.get("/rules")
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

@app.delete("/rules/{name}")
async def delete_rule(name: str, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.name == name).first()
    try:
        if rule:
            db.delete(rule)
            db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=jsonable_encoder({"msg": "Rule deleted"}),
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=jsonable_encoder({"msg": "Rule not found"}),
            )
    except Exception as e:
        logging.error(f"Error deleting rule({rule}): {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": f"Error deleting rule"}),
        )

@app.post("/receivers")
async def create_receiver(
    ireceiver: IReceiver,
    db: Session = Depends(get_db),
):
    try:
        receiver = Receiver(**ireceiver.model_dump())
        db.add(receiver)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder({"msg": "Receiver created"}),
        )
    except Exception as e:
        logging.error(f"Error creating receiver({receiver}): {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": f"Error creating receiver"}),
        )


@app.get("/receivers")
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


@app.delete("/receivers/{name}")
async def delete_receiver(name: str, db: Session = Depends(get_db)):
    receiver = db.query(Receiver).filter(Receiver.name == name).first()
    try:
        if receiver:
            db.delete(receiver)
            db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=jsonable_encoder({"msg": "Receiver deleted"}),
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=jsonable_encoder({"msg": "Receiver not found"}),
            )
    except Exception as e:
        logging.error(f"Error deleting receiver({receiver}): {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"msg": f"Error deleting receiver"}),
        )
        

@app.get("/alerts", response_model=Page[Alert])
async def get_alerts(db: Session = Depends(get_db), chain: Optional[str] = Query(default=None), rule_name: Optional[str] = Query(default=None)):
    # find all alerts for a given chain and rule_name (if specified) with pagination
    query = db.query(Alert)
    if chain:
        query = query.filter(Alert.chain == chain)
    if rule_name:
        query = query.filter(Alert.rule_name == rule_name)
    alerts = paginate(db, query.order_by(Alert.block_number.desc()))
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(alerts),
    )

@cli.command("inject", help="Inject random data for testing")
def inject(
    database_url: str = os.getenv("DATABASE_URL"),
    n_receivers: int = 10,
    n_rules: int = 10,
    n_alerts: int = 100,
):
    from faker import Faker
    from faker.providers import DynamicProvider
    import random
    random.seed(0)
    Faker.seed(0)

    create_db_engine(database_url, auto_create=True)

    fake = Faker()
    fake.add_provider(DynamicProvider(provider_name="chain", elements=["eth", "bsc", "polygon", "optimistic", "avalanche"]))
    fake.add_provider(DynamicProvider(provider_name="scope", elements=["block", "transaction", "receipt"]))
    
    db = SessionLocal()

    # Inject receivers
    try:
        for _ in range(n_receivers):
            name = fake.unique.company()
            url = fake.unique.url()
            init_args = fake.pydict(nb_elements=3, variable_nb_elements=True, value_types=(str, str))
            ireceiver = IReceiver(
                name=name,
                receiver=url,
                init_args=init_args,
            )
            db.add(Receiver(**ireceiver.model_dump()))
        db.commit()
        typer.echo(f"Inject receivers complete")
    except Exception as e:
        db.rollback()
        typer.echo(f"Inject receivers failed, {e}")
        
    # Inject rules
    try:
        recvrs = [r.name for r in db.query(Receiver).all()]
        for _ in range(n_rules):
            name = fake.unique.name()
            scope = fake.scope()
            where = fake.pystr()
            output = fake.sentence(nb_words=10)
            labels = fake.pydict(nb_elements=3, value_types=(str, str))
            desc = fake.sentence(nb_words=10)
            chain = fake.chain()
            irule = IRule(
                name=name,
                scope=scope,
                description=desc,
                where=where,
                output=output,
                labels=labels,
                receivers=random.choices(recvrs, k=random.randint(1, 5)),
                chain=chain,
            )
            db.add(Rule(**irule.model_dump()))
        db.commit()
        typer.echo(f"Inject rules complete")
    except Exception as e:
        db.rollback()
        typer.echo(f"Inject rules failed, {e}")
    
    # Inject alerts
    try:
        rules = [r.name for r in db.query(Rule).all()]
        for _ in range(n_alerts):
            block_timestamp = fake.date_time_between(start_date="-1y", end_date="now")
            block_number = fake.pyint()
            hash = fake.sha256(raw_output=False)
            rule_name = random.choice(rules)
            chain = fake.chain()
            scope = fake.scope()
            output = fake.sentence(nb_words=10)
            labels = fake.pydict(nb_elements=3, value_types=(str, str))
            alert = Alert(
                block_timestamp=block_timestamp,
                block_number=block_number,
                hash=hash,
                rule_name=rule_name,
                chain=chain,
                scope=scope,
                output=output,
                labels=labels,
            )
            db.add(alert)
        db.commit()
        typer.echo(f"Inject alerts complete")
    except Exception as e:
        db.rollback()
        typer.echo(f"Inject alerts failed, {e}")

@cli.command(name="start")
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
