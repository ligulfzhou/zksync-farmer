from enum import Enum


class TransactionType(Enum):
    mint_nft: str = 'MintNFT'
    transfer: str = 'Transfer'
    transfer_nft: str = 'TransferNFT'


# for pickup the transaction type for interaction.
normal_type_cnt = {
    TransactionType.mint_nft.value: 30,
    TransactionType.transfer.value: 60,
    TransactionType.transfer_nft.value: 10
}


GAS_LIMIT_IN_ETHER = 0.00085


class TokenAddressMainNet(Enum):
    eth: str = '0x0000000000000000000000000000000000000000'
    weth: str = '0x5aea5775959fbc2557cc8789bc1bf90a239d9a91'
    usdc: str = '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4'
    zat: str = '0x47ef4a5641992a72cfd57b9406c9d9cefee8e0c4'


class TokenAddressTestNet(Enum):
    eth: str = '0x0000000000000000000000000000000000000000'
    weth: str = '0x20b28b1e4665fff290650586ad76e977eab90c5d'
    usdc: str = '0x0faF6df7054946141266420b43783387A78d82A9'
    zat: str = '0x47ef4a5641992a72cfd57b9406c9d9cefee8e0c4'


TokenAddress = TokenAddressMainNet
# if conf.env == 'era_testnet':
#     TokenAddress = TokenAddressTestNet
