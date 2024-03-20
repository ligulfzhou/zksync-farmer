import os
import json
import random
from typing import List, TypedDict
from dataclasses import dataclass

env = os.getenv('env', 'goerli')
j = json.loads(open(f'{os.path.dirname(__file__)}/{env}.json').read())


class SyncSwapAddress(TypedDict):
    # WETH: str
    # USDC: str
    SyncSwapVault: str
    SyncSwapPoolMaster: str
    SyncSwapClassicPoolFactory: str
    SyncSwapStablePoolFactory: str
    SyncSwapRouter: str


class SyncSwapConfig(TypedDict):
    address: SyncSwapAddress


class MuteConfig(TypedDict):
    Router: str
    Factory: str
    # WETH: str
    # USDC: str
    Multicall: str


@dataclass
class Config:
    env: str
    eth_rpc: str  # json rpc
    zksync_rpcs: List[str]
    mnemonic_code: str  # mnemonic code
    source_key: str  # 'private key'
    abi_file: str
    contract_address: str
    send: List[int]
    send_by_account: int
    deposits: List[int]
    syncswap: SyncSwapConfig
    mute: MuteConfig

    def __init__(self, js: dict):
        self.env = env
        self.eth_rpc = js['rpc_url']
        self.zksync_rpcs = js['zksync_rpc_url']
        self.mnemonic_code = js['mnemonic_code']
        self.source_key = js['source_key']
        self.abi_file = js['abi_file']
        self.contract_address = js['contract']
        self.send = js['send']
        self.send_by_account = js['send_by_account']
        self.deposits = js['deposits']
        self.syncswap = js['syncswap']
        self.mute = js['mute']

    def get_zksync_rpc(self) -> str:
        return random.choice(self.zksync_rpcs)

    # def get_era_cli(self) -> Web3:
    #     if self.env == 'era':
    #         rpc = self.get_zksync_rpc()
    #     else:
    #         rpc = None
    #     w3 = Web3(Web3.HTTPProvider(conf.get_zksync_rpc()))
    #     w3.eth.account.enable_unaudited_hdwallet_features()
    #     return w3


conf = Config(j)

# "https://zksync2-mainnet.zksync.io",
# "https://zksync-era.rpc.thirdweb.com/ed043a51ae23b0db3873f5a38b77ab28175fa496f15d3c53cf70401be89b622a"
