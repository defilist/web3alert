from typing import List, Dict
from sqlalchemy.engine import Engine
from datetime import datetime
import logging
import uuid

from blockchainetl.alert.receivers import BaseReceiver
from blockchainetl.alert.rule import Rule
from blockchainetl.streaming.postgres_utils import create_insert_statement_for_table
from hack.model import Alert

from sqlalchemy import Table


def model_to_table(model_class):
    table_name = model_class.__tablename__
    metadata = model_class.metadata
    return Table(table_name, metadata, autoload=True)


class PostgresReceiver(BaseReceiver):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.stmt = create_insert_statement_for_table(
            model_to_table(Alert),
            on_conflict_do_update=False,
        )
        super().__init__()

    def post(self, rule: Rule, result: List[Dict]):
        items = []
        for item in result:
            # item is in nested dict
            # FIXME: use dict2obj instead?
            inner = list(item.values())[0]
            st = inner.get("block_timestamp", inner.get("timestamp"))
            if st is None:
                logging.warning(f"missing timestamp {inner}")
                continue

            if isinstance(st, int):
                st = datetime.utcfromtimestamp(st)

            blknum = inner.get("block_number", inner.get("number"))
            hash = inner.get("transaction_hash", inner.get("hash"))
            labels = rule.labels.format(item)
            labels = {
                k: v
                for k, v in labels.items()
                if k not in set(["datetime", "blknum", "txhash"])
            }
            output = rule.output.format(item)
            alert = dict(
                id=str(uuid.uuid4()),
                block_timestamp=st,
                block_number=blknum,
                hash=hash,
                rule_name=rule.id,
                scope=rule.scope,
                chain=rule.chain,
                output=output,
                labels=labels,
            )
            items.append(alert)

        with self.engine.connect() as conn:
            result = conn.execute(self.stmt, items)
            return result.rowcount
