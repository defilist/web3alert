#!/usr/bin/env python3

import os
from time import time
import logging
import click
import pypeln as pl
from collections import defaultdict

from cachetools import cached, TTLCache
from datetime import datetime, date
from typing import Dict, Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from threading import Lock
from sqlalchemy.sql import func
from decimal import Decimal

from sqlalchemy import (
    Table,
    Column,
    DateTime,
    BigInteger,
    MetaData,
    Text,
    JSON,
)

from blockchainetl.enumeration.chain import Chain
from blockchainetl.cli.utils import global_click_options
from blockchainetl.utils import time_elapsed
from blockchainetl.streaming.streamer import Streamer
from blockchainetl.jobs.exporters.console_item_exporter import ConsoleItemExporter
from blockchainetl.jobs.exporters.postgres_item_exporter import PostgresItemExporter
from blockchainetl.streaming.postgres_utils import create_insert_statement_for_table
from blockchainetl.service.simple_price_service import SimplePriceService
from ethereumetl.misc.eth_extract_balance import READ_BLOCK_TEMPLATE

from hack.inout_flow import FETCH_INOUT_FLOW_SQL, READ_FUNC_SQL, READ_TXS_SQL
from hack.token_mapping import NOVA_ARBITRUM_TOKEN_MAPPING

TX_KEYS = [
    "tx_from",
    "tx_to",
    "tx_status",
    "tx_fee",
    "tx_fee_token_name",
    "tx_fee_amount",
    "tx_fee_sharable",
    "action",
]

ALERT = "alert"
PLATFORM_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"

ct = func.current_timestamp
ALERTS = Table(
    "alerts",
    MetaData(),
    Column("id", BigInteger),
    Column("rule_id", Text, primary_key=True),
    Column("data", JSON),
    Column("created_at", DateTime, primary_key=True, server_default=ct()),
)


def get_sharable_dict(items: List[Dict]) -> Dict[str, int]:
    sharable_dict = defaultdict(int)
    for item in items:
        key = item["txhash"]
        sharable_dict[key] += 1
    return sharable_dict


def get_min_blknum_of_day(engine: Engine, chain: str, day: str) -> int:
    sql = (
        f"SELECT min(blknum) AS blknum FROM {chain}.blocks "
        f"WHERE block_timestamp >= '{day} 00:00:00' AND block_tiemstamp <= '{day} 23:59:59' "
    )
    with engine.connect() as conn:
        row = conn.execute(text(sql)).fetchone()  # type: ignore
    assert row is not None
    return row["blknum"]


class InoutFlowAdapter:
    def __init__(
        self,
        chain,
        data_engine: Engine,
        meta_engine: Engine,
        oracle_engine: Engine,
        meta_schema: str,
        price_service: SimplePriceService,
        item_exporter=ConsoleItemExporter(),
        batch_size=100,
        max_workers=5,
        is_pending_mode=False,
        drop_zero_value=False,
        drop_failed_transaction=False,
    ):
        self.data_engine = data_engine
        self.meta_engine = meta_engine
        self.oracle_engine = oracle_engine
        self.meta_schema = meta_schema
        self.ps = price_service
        self.chain = chain
        self.item_exporter = item_exporter
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.is_pending_mode = is_pending_mode
        self.drop_zero_value = drop_zero_value
        self.drop_failed_transaction = drop_failed_transaction
        self.chain_symbol = Chain.symbol(chain)

    def open(self):
        self.item_exporter.open()

    # cache for 10s
    @cached(cache=TTLCache(maxsize=16, ttl=10))
    def get_current_block_number(self) -> int:
        sql = (
            f"SELECT blknum, _st AS timestamp FROM {self._schema()}.blocks "
            "ORDER BY block_timestamp DESC LIMIT 1"
        )
        with self.data_engine.connect() as conn:
            row = conn.execute(text(sql)).fetchone()  # type: ignore
        return (row["blknum"], row["timestamp"])  # type: ignore

    def export_all(self, start_block, end_block):
        st, et = self._export_block_time_range(start_block, end_block)

        if isinstance(st, int):
            st = datetime.utcfromtimestamp(st)
        if isinstance(et, int):
            et = datetime.utcfromtimestamp(et)
        st_time = str(st)
        et_time = str(et)
        rule_details = self.get_rule_details()
        for rule_detail in rule_details:
            self.export_all_rule(start_block, end_block, st_time, et_time, rule_detail)

    def export_all_rule(
        self,
        start_block: int,
        end_block: int,
        st_time: str,
        et_time: str,
        rule_detail: Dict,
    ):
        rule_id = rule_detail["rule_id"]
        detail = rule_detail["detail"]
        source_addres = {e["address"]: e["tag"] for e in detail["addresses"]}
        threshold = detail["threshold"]
        st1 = time()
        if len(source_addres) == 0:
            logging.info("no source address found, skipped")
            return

        sql = FETCH_INOUT_FLOW_SQL.render(
            chain=self.chain,
            addres=list(source_addres.keys()) if len(source_addres) < 100 else None,
            st_time=st_time,
            et_time=et_time,
            st_blk=start_block,
            et_blk=end_block,
            chain_symbol=self.chain_symbol,
            drop_value_zero=self.drop_zero_value,
            drop_failed_transaction=self.drop_failed_transaction,
        )

        with self.data_engine.connect() as conn:
            result = conn.execute(text(sql))
        inout_flows = [x._asdict() for x in result.fetchall()]  # type: ignore

        st2 = time()
        items = pl.thread.filter(
            lambda x: False
            or x["from_address"] in source_addres
            or x["to_address"] in source_addres,
            inout_flows,
            workers=self.max_workers,
        )
        items = list(items)
        st3 = time()

        if len(items) == 0:
            return

        txs_sql = READ_TXS_SQL.render(
            chain=self.chain,
            st_time=st_time,
            et_time=et_time,
            st_blk=start_block,
            et_blk=end_block,
            chain_symbol=self.chain_symbol,
        )
        tx_dict = {}
        with self.data_engine.connect() as conn:
            result = conn.execute(text(txs_sql))
        for x in result.fetchall():  # type: ignore
            tx_dict.setdefault(x["txhash"], x)

        sharable_dict = get_sharable_dict(items)

        def _enrich_txinfo(item: Dict) -> Dict:
            txhash = item["txhash"]
            tx = tx_dict.get(txhash, None)
            if not tx:
                raise Exception(
                    f"not found the transaction {txhash} in the {self.chain}.txs"
                )
            for key in TX_KEYS:
                if key == "action":
                    item[key] = self._enrich_tx_action(tx[key])
                elif key == "tx_fee_sharable":
                    item[key] = sharable_dict[txhash] > 1
                else:
                    item[key] = tx[key]
            return item

        items = pl.thread.map(_enrich_txinfo, items, workers=self.max_workers)

        def _enrich_item(item: Dict) -> Dict:
            item["chain"] = self.chain

            dk = "block_timestamp"
            if dk in item and isinstance(item[dk], (datetime, date)):
                item[dk] = item[dk].strftime("%Y-%m-%d %H:%M:%S")

            item = self._enrich_value_price(item)
            item = self._enrich_txfee_price(item)

            # enrich direction
            from_in_cluster = item["from_address"] in source_addres
            to_in_cluster = item["to_address"] in source_addres
            if from_in_cluster and to_in_cluster:
                item["direction"] = "inner"
            elif from_in_cluster:
                item["direction"] = "out"
            elif to_in_cluster:
                item["direction"] = "in"
            else:
                item["direction"] = "unknown"

            if from_in_cluster:
                item["from_tag"] = source_addres[item["from_address"]]
            else:
                item["from_tag"] = None
            if to_in_cluster:
                item["to_tag"] = source_addres[item["to_address"]]
            else:
                item["to_tag"] = None

            return item

        items = pl.thread.map(_enrich_item, items, workers=self.max_workers)
        items = pl.thread.filter(
            lambda x: x["value_usd"] or 0 >= threshold,
            items,
            workers=self.max_workers,
        )

        items = pl.thread.map(self._enrich_label, items, workers=2)

        def _convert(item: Dict) -> Dict:
            for dk, v in item.items():
                if isinstance(v, (datetime, date)):
                    item[dk] = v.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(v, Decimal):
                    if str(v) == str(int(v)):
                        item[dk] = int(v)
                    else:
                        item[dk] = float(round(v, 6))
            return item

        items = pl.thread.map(_convert, items, workers=2)
        items = [{"type": ALERT, "data": e, "rule_id": rule_id} for e in items]

        st4 = time()

        self.item_exporter.export_items(items)
        st5 = time()

        logging.info(
            f"Export {start_block, end_block} of rule: {rule_id} "
            f"#inout_flows={len(inout_flows)} #items={len(items)} "
            f"elapsed @total={time_elapsed(st1, st5)} @db_read={time_elapsed(st1, st2)} "
            f"@filter={time_elapsed(st2, st3)} @enrich={time_elapsed(st3, st4)} "
            f"@export={time_elapsed(st4, st5)}"
        )

    # cache for 60min
    @cached(cache=TTLCache(maxsize=1024, ttl=3600), lock=Lock())
    def get_address_label(self, address) -> Optional[str]:
        sql = (
            f"SELECT address, string_agg(label, ';') AS label FROM {self.chain}.addr_labels "
            f"WHERE address = '{address}' GROUP BY 1"
        )
        with self.oracle_engine.connect() as conn:
            row = conn.execute(text(sql)).fetchone()  # type: ignore
        if row is not None:
            return row["label"]
        return None

    # cache for 30min
    @cached(cache=TTLCache(maxsize=16, ttl=1800), lock=Lock())
    def get_rule_details(self) -> List[Dict]:
        sql = (
            f"SELECT id AS rule_id, detail FROM {self.meta_schema}.rules "
            + f"WHERE ruleset = 'inout_flow' AND chain = '{self.chain}'"
        )
        with self.meta_engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()  # type: ignore
        return rows

    @cached(cache=TTLCache(maxsize=1024, ttl=1800), lock=Lock())
    def _enrich_tx_action(self, byte_sign) -> str:
        if byte_sign in ("", "0x"):
            return "Transfer"

        with self.oracle_engine.connect() as conn:
            row = conn.execute(READ_FUNC_SQL.render(byte_sign=byte_sign)).fetchone()  # type: ignore
        if row is None:
            # if not found, return the original one
            return byte_sign
        return row["text_sign"]

    def _export_block_time_range(self, start_block, end_block):
        sql = READ_BLOCK_TEMPLATE.render(
            chain=self._schema(),
            st_blknum=start_block,
            et_blknum=end_block,
        )
        with self.data_engine.connect() as conn:
            result = conn.execute(text(sql))
        row = result.fetchone()  # type: ignore
        assert row is not None
        return row["min_st"], row["max_st"]

    def _enrich_txfee_price(self, item: Dict) -> Dict:
        chain = self.chain
        if self.chain == Chain.NOVA:
            chain = Chain.ARBITRUM
        price = self.ps.get_price(
            chain,
            PLATFORM_TOKEN_ADDRESS,
            item["block_timestamp"],
        )
        if price and item.get("tx_fee_amount") is not None:
            item["tx_fee_usd"] = float(item["tx_fee_amount"]) * price
        else:
            item["tx_fee_usd"] = None
        return item

    def _enrich_value_price(self, item: Dict) -> Dict:
        chain = self.chain
        token = item["token_address"]
        # replace arbitrum-nova's chain to arbitrum
        if self.chain == Chain.NOVA and token in NOVA_ARBITRUM_TOKEN_MAPPING:
            chain = Chain.ARBITRUM
            token = NOVA_ARBITRUM_TOKEN_MAPPING[token]
        # enrich price
        price = self.ps.get_price(chain, token, item["block_timestamp"])
        if price:
            item["value_usd"] = float(item["value_amount"]) * price
            item["price"] = price
        else:
            item["value_usd"] = None
            item["price"] = None
        return item

    def _enrich_label(self, item: Dict) -> Dict:
        item["from_label"] = self.get_address_label(item["from_address"])
        item["to_label"] = self.get_address_label(item["to_address"])
        return item

    def close(self):
        self.item_exporter.close()

    def _schema(self):
        schema = self.chain
        if self.is_pending_mode is True:
            schema += "_pending"
        return schema


# pass kwargs, ref https://stackoverflow.com/a/36522299/2298986
@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@global_click_options
@click.option(
    "-l",
    "--last-synced-block-file",
    default=".priv/inout-flow.txt",
    required=True,
    show_default=True,
    help="The file used to store the last synchronized block file",
)
@click.option(
    "--lag",
    default=10,
    show_default=True,
    type=int,
    help="The number of blocks to lag behind the network.",
)
@click.option(
    "--price-url",
    type=str,
    required=True,
    help="The price connection url, used in brahma service",
)
@click.option(
    "--db-data-url",
    type=str,
    default="postgresql://postgres:root@127.0.0.1:5432/postgres",
    envvar="BLOCKCHAIN_ETL_PG_URL",
    show_default=True,
    help="The Postgres connection url(used to read source items)",
)
@click.option(
    "--db-meta-url",
    type=str,
    default="postgresql://postgres:root@127.0.0.1:5432/postgres",
    envvar="BLOCKCHAIN_ETL_PG_URL",
    show_default=True,
    help="The Postgres connection url(used to write results)",
)
@click.option(
    "--db-meta-schema",
    type=str,
    default="web3soc",
    show_default=True,
    help="The Postgres schema",
)
@click.option(
    "--db-oracle-url",
    type=str,
    default="postgresql://postgres:root@127.0.0.1:5432/postgres",
    show_default=True,
    help="The Postgres connection url(used to read source addresses)",
)
@click.option(
    "-s",
    "--start-block",
    default=-1,
    show_default=True,
    type=int,
    help="Start block, included",
)
@click.option(
    "-e",
    "--end-block",
    default=None,
    show_default=True,
    type=int,
    help="End block, included",
)
@click.option(
    "--start-date",
    default=None,
    show_default=True,
    help="Start datetime(included), used in daily mode",
)
@click.option(
    "--end-date",
    default=None,
    show_default=True,
    help="End datetime(excluded), used in daily mode",
)
@click.option(
    "--drop-zero-value",
    is_flag=True,
    show_default=True,
    type=bool,
    help="Get the transactions of which values are less than 1",
)
@click.option(
    "--drop-failed-transaction",
    is_flag=True,
    show_default=True,
    type=bool,
    help="Get the transactions of which status are failed",
)
@click.option(
    "--period-seconds",
    default=90,
    show_default=True,
    type=int,
    help="How many seconds to sleep between syncs",
)
@click.option(
    "-b",
    "--batch-size",
    default=50,
    show_default=True,
    type=int,
    help="How many query items are carried in a JSON RPC request, "
    "the JSON RPC Server is required to support batch requests",
)
@click.option(
    "-B",
    "--block-batch-size",
    default=10,
    show_default=True,
    type=int,
    help="How many blocks to batch in single sync round, write how many blocks in one CSV file",
)
@click.option(
    "-w",
    "--max-workers",
    default=5,
    show_default=True,
    type=int,
    help="The number of workers",
)
@click.option(
    "--print-sql",
    is_flag=True,
    show_default=True,
    help="Print SQL or not",
)
def dump(
    chain,
    last_synced_block_file,
    lag,
    price_url,
    db_data_url,
    db_meta_url,
    db_meta_schema,
    db_oracle_url,
    start_block,
    end_block,
    start_date,
    end_date,
    period_seconds,
    batch_size,
    block_batch_size,
    max_workers,
    drop_zero_value,
    drop_failed_transaction,
    print_sql,
):
    """Fetch in-outflow of specified addresses"""
    item_exporter = PostgresItemExporter(
        db_meta_url,
        db_meta_schema,
        item_type_to_insert_stmt_mapping={
            ALERT: create_insert_statement_for_table(
                ALERTS,
                on_conflict_do_update=False,
            ),
        },
        print_sql=print_sql,
    )

    data_engine = create_engine(db_data_url)
    if db_meta_url == db_data_url:
        meta_engine = data_engine
    else:
        meta_engine = create_engine(db_meta_url)
    if db_oracle_url == db_data_url:
        oracle_engine = data_engine
    else:
        oracle_engine = create_engine(db_oracle_url)

    price_service = SimplePriceService()

    streamer_adapter = InoutFlowAdapter(
        chain,
        data_engine,
        meta_engine,
        oracle_engine,
        db_meta_schema,
        price_service,
        item_exporter=item_exporter,
        batch_size=batch_size,
        max_workers=max_workers,
        drop_zero_value=drop_zero_value,
        drop_failed_transaction=drop_failed_transaction,
    )

    if (
        not os.path.exists(last_synced_block_file)
        and start_date is not None
        and end_date is not None
    ):
        logging.info(f"Daily export from: {start_date} to {end_date}")
        start_block = get_min_blknum_of_day(data_engine, chain, start_date)
        end_block = get_min_blknum_of_day(data_engine, chain, end_date)

    streamer = Streamer(
        blockchain_streamer_adapter=streamer_adapter,
        last_synced_block_file=last_synced_block_file,
        lag=lag,
        start_block=start_block,
        end_block=end_block,
        period_seconds=period_seconds,
        block_batch_size=block_batch_size,
    )
    streamer.stream()


dump()
