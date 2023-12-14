from jinja2 import Template

FETCH_INOUT_FLOW_SQL = Template(
    """
WITH
{% if addres is not none %}
addres(address) AS ( VALUES
{%- for addr in addres %}
    ('{{addr}}'){%- if loop.last is false -%},{%- endif -%}
{%- endfor %}
),
{% endif %}
traces AS (
    SELECT DISTINCT
        block_timestamp,
        blknum,
        txhash,
        txpos,
        '[]'::text AS trace_address,
        -1::bigint AS logpos,
        from_address,
        COALESCE(to_address, receipt_contract_address) AS to_address,
        '{{chain_symbol}}'::text AS token_name,
        '0x0000000000000000000000000000000000000000'::text AS token_address,
        CASE receipt_status WHEN 0 THEN 0 ELSE value END AS value,
        CASE receipt_status WHEN 0 THEN 0 ELSE value/1e18 END AS value_amount,
        COALESCE(receipt_status, 1) AS trace_status
    FROM
        {{chain}}.txs
    WHERE
        from_address is not null
        AND block_timestamp >= '{{st_time}}' AND block_timestamp <= '{{et_time}}'
        AND blknum >= {{st_blk}} AND blknum <= {{et_blk}}
{% if not drop_failed_transaction %}
        AND (receipt_status = 1 OR receipt_status is null)
{% endif %}
{% if addres is not none %}
        AND (
            from_address IN (SELECT address FROM addres)
            OR to_address IN (SELECT address FROM addres)
        )
{% endif %}
    UNION ALL
    SELECT DISTINCT
        block_timestamp,
        blknum,
        txhash,
        txpos,
        trace_address,
        -1::bigint AS logpos,
        from_address,
        to_address,
        '{{chain_symbol}}'::text AS token_name,
        '0x0000000000000000000000000000000000000000'::text AS token_address,
        value,
        value/1e18 AS value_amount,
        COALESCE(status, 1) AS trace_status
    FROM
        {{chain}}.traces
    WHERE
        block_timestamp >= '{{st_time}}' AND block_timestamp <= '{{et_time}}'
        AND blknum >= {{st_blk}} AND blknum <= {{et_blk}}
        AND trace_address <> '[]'
{% if not drop_failed_transaction %}
        AND (status = 1 OR status is null)
{% endif %}
{% if not drop_zero_value %}
        AND value > 0
{% endif %}
{% if addres is not none %}
        AND (
            from_address IN (SELECT address FROM addres)
            OR to_address IN (SELECT address FROM addres)
        )
{% endif %}
), token_xfers AS (
    SELECT DISTINCT
        block_timestamp,
        blknum,
        txhash,
        txpos,
        ''::text AS trace_address,
        logpos,
        from_address,
        to_address,
        COALESCE(symbol, name) AS token_name,
        token_address,
        value,
        value/power(10, decimals) AS value_amount,
        1 AS trace_status
    FROM
        {{chain}}.token_xfers
    WHERE
        block_timestamp >= '{{st_time}}' AND block_timestamp <= '{{et_time}}'
        AND blknum >= {{st_blk}} AND blknum <= {{et_blk}}
        AND decimals is not null
{% if not drop_zero_value %}
        AND value > 0
{% endif %}
{% if addres is not none %}
        AND (
            from_address IN (SELECT address FROM addres)
            OR to_address IN (SELECT address FROM addres)
        )
{% endif %}
), xfers AS (
    SELECT * FROM traces
    UNION
    SELECT * FROM token_xfers
)

SELECT DISTINCT
    block_timestamp,
    blknum,
    txhash,
    txpos,
    trace_address,
    logpos,
    from_address,
    to_address,
    token_name,
    token_address,
    value,
    value_amount,
    trace_status
FROM
    xfers
    """
)

READ_FUNC_SQL = Template(
    """
SELECT
    byte_sign,
    SUBSTRING(text_sign, 0, POSITION('(' in text_sign)) AS text_sign
FROM
    metax.func_signatures
WHERE
    byte_sign = '{{byte_sign}}'
"""
)

READ_TXS_SQL = Template(
    """
SELECT DISTINCT
    txhash,
    tx_from,
    tx_to,
    action,
    tx_status,
    tx_fee_token_name,
    gas_price * gas_used AS tx_fee,
    gas_price * gas_used / 1e18 AS tx_fee_amount
FROM (
    SELECT
        txhash,
        from_address AS tx_from,
        COALESCE(to_address, receipt_contract_address) AS tx_to,
        substring(input FROM 1 FOR 10) AS action,
        CASE receipt_status WHEN null THEN 1 WHEN 1 THEN 1 ELSE 0 END AS tx_status,
        '{{chain_symbol}}'::text AS tx_fee_token_name,
        COALESCE(receipt_effective_gas_price, gas_price)::NUMERIC AS gas_price,
        receipt_gas_used::NUMERIC AS gas_used
    FROM
        {{chain}}.txs
    WHERE
        block_timestamp >= '{{st_time}}' AND block_timestamp <= '{{et_time}}'
        AND blknum >= {{st_blk}} AND blknum <= {{et_blk}}
) _
"""
)
