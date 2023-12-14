NOVA_ARBITRUM_TOKEN_MAPPING = {
    "0x0000000000000000000000000000000000000000": "0x0000000000000000000000000000000000000000",  # ETH # noqa
    "0x765277eebeca2e31912c9946eae1021199b39c61": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",  # WETH # noqa
}


# fetch from with jsonrpc as below:
# endpoint: https://10.132.83.97:8000/zksync-era
# body: { "jsonrpc":"2.0", "method":"zks_getConfirmedTokens", "params": [0, 100], "id":1 }
ZKSYNCERA_ETHEREUM_MAPPING = {
    "0x0000000000000000000000000000000000000000": {
        "decimals": 18,
        "l1Address": "0x0000000000000000000000000000000000000000",
        "l2Address": "0x0000000000000000000000000000000000000000",
        "name": "Ether",
        "symbol": "ETH",
    },
    "0xaff169fca5086940c890c8a04c6db4b1db6e0dd6": {
        "decimals": 18,
        "l1Address": "0xba100000625a3754423978a60c9317c58a424e3d",
        "l2Address": "0xaff169fca5086940c890c8a04c6db4b1db6e0dd6",
        "name": "Balancer",
        "symbol": "BAL",
    },
    "0x0e97c7a0f8b2c9885c8ac9fc6136e829cbc21d42": {
        "decimals": 18,
        "l1Address": "0xa49d7499271ae71cd8ab9ac515e6694c755d400c",
        "l2Address": "0x0e97c7a0f8b2c9885c8ac9fc6136e829cbc21d42",
        "name": "Mute.io",
        "symbol": "MUTE",
    },
    "0xc2b13bb90e33f1e191b8aa8f44ce11534d5698e3": {
        "decimals": 18,
        "l1Address": "0xffffffff2ba8f66d4e51811c5190992176930278",
        "l2Address": "0xc2b13bb90e33f1e191b8aa8f44ce11534d5698e3",
        "name": "Furucombo",
        "symbol": "COMBO",
    },
    "0x42c1c56be243c250ab24d2ecdcc77f9ccaa59601": {
        "decimals": 18,
        "l1Address": "0xbc396689893d065f41bc2c6ecbee5e0085233447",
        "l2Address": "0x42c1c56be243c250ab24d2ecdcc77f9ccaa59601",
        "name": "Perpetual",
        "symbol": "PERP",
    },
    "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4": {
        "decimals": 6,
        "l1Address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "l2Address": "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4",
        "name": "USD Coin",
        "symbol": "USDC",
    },
    # EMP doesn't support those tokens currently(2023.04.18)
    # "0x503234f203fc7eb888eec8513210612a43cf6115": {
    #     "decimals": 18,
    #     "l1Address": "0x5f98805a4e8be255a32880fdec7f6728c6568ba0",
    #     "l2Address": "0x503234f203fc7eb888eec8513210612a43cf6115",
    #     "name": "LUSD Stablecoin",
    #     "symbol": "LUSD",
    # },
    # "0xee1e88eb20becdebe1e88f50c9f8b1d72478f2d0": {
    #     "decimals": 18,
    #     "l1Address": "0x95b3497bbcccc46a8f45f5cf54b0878b39f8d96c",
    #     "l2Address": "0xee1e88eb20becdebe1e88f50c9f8b1d72478f2d0",
    #     "name": "UniDex",
    #     "symbol": "UNIDX",
    # },
}

TOKEN_MAPPING = {
    "bor": {"mSHEESHA": "MSHEESHA"},
}
