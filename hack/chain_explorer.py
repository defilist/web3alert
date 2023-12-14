CHAIN_EXPLORERS = {
    "ethereum": "https://etherscan.io",
    "bsc": "https://bscscan.com",
    "avalanche": "https://snowtrace.io",
    "heco": "https://hecoinfo.com",
    "arbitrum": "https://arbiscan.io",
    "fantom": "https://ftmscan.com",
    "cronos": "https://cronoscan.com",
    "optimistic": "https://optimistic.etherscan.io",
    "bor": "https://polygonscan.com",
    "moonriver": "https://moonriver.moonscan.io",
    "moonbeam": "https://moonbeam.moonscan.io",
    "aurora": "https://aurorascan.dev",
    "celo": "https://celoscan.io",
}


def link_of_chain_tx(chain: str, txhash: str) -> str:
    base_url = CHAIN_EXPLORERS[chain]
    return f"{base_url}/tx/{txhash}"
