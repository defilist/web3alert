#!/usr/bin/env python

import logging

import click
from web3 import HTTPProvider, Web3
import sqlalchemy as sa

from bitcoinetl.rpc.bitcoin_rpc import BitcoinRpc
from bitcoinetl.streaming.btc_streamer_adapter import BtcStreamerAdapter
from blockchainetl.alert.rule_set import RuleSets
from blockchainetl.cli.utils import (
    extract_cmdline_kwargs,
    global_click_options,
    pick_random_provider_uri,
    str2bool,
)
from blockchainetl.enumeration.chain import Chain
from blockchainetl.enumeration.entity_type import EntityType, parse_entity_types
from blockchainetl.streaming.streamer import Streamer
from blockchainetl.thread_local_proxy import ThreadLocalProxy
from ethereumetl.providers.auto import get_provider_from_uri
from ethereumetl.service.eth_token_service import EthTokenService
from ethereumetl.streaming.eth_streamer_adapter import EthStreamerAdapter

from hack.alert_exporter import AlertExporter


# pass kwargs, ref https://stackoverflow.com/a/36522299/2298986
@click.command(
    context_settings=dict(
        help_option_names=["-h", "--help"],
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.pass_context
@global_click_options
@click.option(
    "-l",
    "--last-synced-block-file",
    default=".priv/etl.txt",
    show_default=True,
    envvar="BLOCKCHAIN_ETL_LAST_ALERTFILE",
    type=str,
    help="The file with the last synced block number.",
)
@click.option(
    "--lag",
    default=0,
    show_default=True,
    type=int,
    help="The number of blocks to lag behind the network.",
)
@click.option(
    "-p",
    "--provider-uri",
    default="https://mainnet.infura.io",
    show_default=True,
    type=str,
    envvar="BLOCKCHAIN_ETL_PROVIDER_URI",
    help="The URI of the JSON-RPC's provider.",
)
@click.option(
    "-s",
    "--start-block",
    default=-1,
    show_default=True,
    type=int,
    help="Start block",
)
@click.option(
    "-e",
    "--end-block",
    default=None,
    show_default=True,
    type=int,
    help="End block",
)
@click.option(
    "-E",
    "--entity-types",
    default=",".join(
        [
            EntityType.BLOCK,
            EntityType.TRANSACTION,
            EntityType.LOG,
            EntityType.TOKEN_TRANSFER,
        ]
    ),
    show_default=True,
    type=str,
    help="The list of entity types to alert.",
)
@click.option(
    "--database-url",
    type=str,
    show_default=True,
    envvar="DATABASE_URL",
    help="The Postgres database URL, used to fetch rules and store alert results",
)
@click.option(
    "--database-schema",
    type=str,
    default="web3",
    show_default=True,
    envvar="DATABASE_SCHEMA",
    help="The Postgres database schema name",
)
@click.option(
    "--period-seconds",
    default=10,
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
    "-w",
    "--max-workers",
    default=5,
    show_default=True,
    type=int,
    help="The number of workers",
)
@click.option(
    "--pid-file",
    default=None,
    show_default=True,
    type=str,
    help="The pid file",
)
@click.option(
    "--token-cache-path",
    type=click.Path(exists=False, readable=True, dir_okay=True, writable=True),
    default="cache/token_cache",
    show_default=True,
    help="The path to store token's attributes",
)
@click.option(
    "--debug",
    is_flag=True,
    show_default=True,
    help="In debug mode",
)
def alert(
    ctx,
    chain,
    last_synced_block_file,
    lag,
    provider_uri,
    start_block,
    end_block,
    entity_types,
    database_url,
    database_schema,
    period_seconds,
    batch_size,
    max_workers,
    pid_file,
    token_cache_path,
    debug,
):
    """Alert the live stream with rules"""
    entity_types = parse_entity_types(entity_types)

    kwargs = extract_cmdline_kwargs(ctx)
    logging.info(f"Start alert with extra kwargs {kwargs}")

    provider_uri = pick_random_provider_uri(provider_uri)
    logging.info("Using provider: " + provider_uri)

    connect_args = {"options": f"-c search_path={database_schema}"}
    engine = sa.create_engine(database_url, connect_args=connect_args)

    token_service = None
    if chain in Chain.ALL_ETHEREUM_FORKS:
        web3 = Web3(HTTPProvider(provider_uri))
        token_service = EthTokenService(web3, cache_path=token_cache_path)

    alert_exporter = AlertExporter(
        chain,
        engine,
        max_workers=max_workers,
        token_service=token_service,
        enable_print=debug,
    )

    if chain in Chain.ALL_ETHEREUM_FORKS:
        streamer_adapter = EthStreamerAdapter(
            batch_web3_provider=ThreadLocalProxy(
                lambda: get_provider_from_uri(provider_uri, batch=True)
            ),
            item_exporter=alert_exporter,
            chain=chain,
            batch_size=batch_size,
            max_workers=max_workers,
            entity_types=entity_types,
            is_geth_provider=str2bool(kwargs.get("provider_is_geth")),
            check_transaction_consistency=str2bool(
                kwargs.get("check_transaction_consistency")
            ),
            ignore_receipt_missing_error=str2bool(
                kwargs.get("ignore_receipt_missing_error")
            ),
        )
    elif chain in Chain.ALL_BITCOIN_FORKS:
        streamer_adapter = BtcStreamerAdapter(
            bitcoin_rpc=ThreadLocalProxy(lambda: BitcoinRpc(provider_uri)),
            item_exporter=alert_exporter,
            chain=chain,
            enable_enrich=True,
            batch_size=batch_size,
            max_workers=max_workers,
        )
    else:
        raise NotImplementedError(
            f"--chain({chain}) is not supported in entity types({entity_types})) "
        )

    streamer = Streamer(
        blockchain_streamer_adapter=streamer_adapter,
        last_synced_block_file=last_synced_block_file,
        lag=lag,
        start_block=start_block,
        end_block=end_block,
        period_seconds=period_seconds,
        block_batch_size=1,
        pid_file=pid_file,
    )
    streamer.stream()

    RuleSets.close()


alert()
