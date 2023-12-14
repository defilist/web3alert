#!/bin/bash

set -e

# Jump to the current directory first
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" >/dev/null 2>&1 && pwd )"
cd "${DIR}" || exit

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"

export PYTHONPATH=.
export PIPENV_VENV_IN_PROJECT=1
export PIPENV_IGNORE_VIRTUALENVS=1

if [[ ! -f .env ]]; then
    >&2 echo ".env file not found"
    exit 1
fi

# https://gist.github.com/mihow/9c7f559807069a03e302605691f85572#gistcomment-2706921
# shellcheck disable=SC2046
export $(sed 's/#.*//g' .env | xargs)

mkdir -p logs

exec pipenv run ./hack/fetch-inout-flow.py \
    --chain=ethereum \
    --lag=40 \
    --price-url="http://10.132.83.97:9000" \
    --last-synced-block-file=.priv/ethereum/inout-flow.txt \
    --start-block=-1 \
    --db-oracle-url="$BLOCKCHAIN_ETL_TSDB_URL" \
    --db-data-url="$BLOCKCHAIN_ETL_DSDB_URL" \
    --db-meta-url="$WEB3SOC_DB_URL" \
    --db-meta-schema="web3soc"
