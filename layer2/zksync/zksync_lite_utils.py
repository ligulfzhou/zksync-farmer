import datetime
import os
import random

import requests
import os.path
from web3 import Web3
from decimal import Decimal
from os import environ
from layer2.logger import global_logger
from layer2.lib.rs import get_ipfs_hash
from layer2.lib.l1_utils import from_mnemonic, w3
from eth_account.signers.local import LocalAccount
from typing import Optional, Union, Dict, List

from layer2.config.config import conf
from zksync_sdk import ZkSyncProviderV01, HttpJsonRPCTransport, network, ZkSync, EthereumProvider, Wallet, ZkSyncSigner, \
    EthereumSignerWeb3, ZkSyncLibrary
from zksync_sdk.zksync_provider.transaction import TransactionResult, TransactionStatus, Transaction
from zksync_sdk.types import ChangePubKeyEcdsa, AccountState, NFT
from layer2.consts import TransactionType


class ZKSyncLiteUtils:

    @classmethod
    def setup_env(cls):
        environ.setdefault('ZK_SYNC_LIBRARY_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                                                'zksync-crypto-c/target/release/libzks_crypto.so'))
        # environ.setdefault('ZK_SYNC_LIBRARY_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)),
        #                                                         'zksync-crypto-c/target/release/libzks_crypto.dylib'))

    @staticmethod
    def _get_wallet(account: LocalAccount) -> Wallet:
        library = ZkSyncLibrary()
        provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))

        ethereum_signer = EthereumSignerWeb3(account=account)

        main_contract = conf.contract_address
        zksync = ZkSync(account=account, web3=w3, zksync_contract_address=Web3.to_checksum_address(main_contract))
        ethereum_provider = EthereumProvider(w3, zksync)

        signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
        wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer,
                        eth_signer=ethereum_signer, provider=provider)
        return wallet

    @classmethod
    async def mint_nft(cls, account: Optional[LocalAccount] = None, idx: int = 0)-> bool:
        if not account:
            account = from_mnemonic(idx=idx)

        global_logger.info(f'===> start to mint nft for {account.address}... <===')
        wallet = cls._get_wallet(account)
        tx: Transaction = await wallet.mint_nft(get_ipfs_hash(), account.address, "ETH")
        status: TransactionResult = await tx.await_committed()
        global_logger.info(f'status: {status.status}')
        if status.status == TransactionStatus.FAILED:
            global_logger.info(f'mint nft for {account.address}, try again after 1 second')
            return False
        return True

    @classmethod
    async def tranfer_nft(cls, account: Optional[LocalAccount] = None, idx: int = 0, target: Optional[LocalAccount] = None,
                          target_idx: int = 0)-> bool:
        if not account:
            account = from_mnemonic(idx=idx)
        if not target:
            target = from_mnemonic(idx=target_idx)

        layer2_account = await cls.get_account(account)
        key_to_nfts: Dict[str, NFT] = layer2_account.verified.minted_nfts
        balance = layer2_account.committed.balances.get('ETH', 0)
        if not key_to_nfts:
            global_logger.error(f'ALERT>>>>, {account.address} does not have any nfts, just skip tranfer nfts...')
            return True

        random_nft: NFT = random.choice(list(key_to_nfts.values()))
        global_logger.info(f'=====> start to tranfer nft: {random_nft.address} from {account.address} to {target.address}... <=====')
        wallet = cls._get_wallet(account)
        txs: List[Transaction] = await wallet.transfer_nft(target.address, random_nft, "ETH")
                                                           # fee=Decimal('0.0001'))
        success = True
        for tx in txs:
            status: TransactionResult = await tx.await_committed()
            global_logger.info(status)
            global_logger.info(f'status: {status.status}')
            if status.status == TransactionStatus.FAILED:
                global_logger.error(f'transfer nft {random_nft.address} for {target.address} failed...')
                success = False
        return success

    @classmethod
    async def tranfer_nft_to_self(cls, account: Optional[LocalAccount] = None, idx: int = 0):
        await cls.tranfer_nft(account, idx, account, idx)

    @classmethod
    async def transfer(cls, account: Optional[LocalAccount] = None, idx: int = 0, target: Optional[LocalAccount] = None,
                       target_idx: int = 0, value_in_eth: Union[float, str] = '0')-> bool:
        # value: "ETH"
        if not account:
            account = from_mnemonic(idx=idx)
        if not target:
            target = from_mnemonic(idx=target_idx)

        global_logger.info(f'=====> start to tranfer {value_in_eth} eth from {account.address} to {target.address}... <=====')
        wallet = cls._get_wallet(account)
        tx: Transaction = await wallet.transfer(target.address, amount=Decimal(value_in_eth), token='ETH')
        status: TransactionResult = await tx.await_committed()
        global_logger.info(status)
        global_logger.info(f'status: {status.status}')
        if status.status == TransactionStatus.FAILED:
            global_logger.error(f'transfer for {target.address} failed...')
            return False
        return True

    @classmethod
    async def activate(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        if not account and not idx:
            return False

        if not account:
            account = from_mnemonic(idx=idx)

        wallet = cls._get_wallet(account)
        already_signed = await wallet.is_signing_key_set()
        if already_signed:
            return True

        tx: Transaction = await wallet.set_signing_key("ETH", eth_auth_data=ChangePubKeyEcdsa())
        global_logger.info(tx)
        status: TransactionResult = await tx.await_committed()
        global_logger.info(f'status: {status.status}')
        if status.status == TransactionStatus.FAILED:
            global_logger.error(f'activation for {account.address} failed...')
            return False
        return True

    @classmethod
    async def transfer_to_self(cls, account: Optional[LocalAccount] = None, idx: int = 0,
                               value_in_eth: Union[float, str] = '0')-> bool:
        return await cls.transfer(account, idx, account, idx, value_in_eth)

    @classmethod
    async def get_balance(cls, account: Optional[LocalAccount]=None, idx: int = 0)-> int:
        account_state = await cls.get_account(account=account, idx=idx)
        balance = account_state.committed.balances.get('ETH', 0)
        return balance

    @classmethod
    async def get_account(cls, account: Optional[LocalAccount] = None, idx: int = 0):
        if not account:
            account = from_mnemonic(idx=idx)

        wallet = cls._get_wallet(account)
        account_state: AccountState = await wallet.get_account_state()
        return account_state

    @classmethod
    def get_nonce(cls, account: Optional[LocalAccount] = None, idx: int = 0, proxy: Optional[Dict] = None) -> int:
        tx = cls.get_last_tx(account, idx, proxy)
        return tx.get('tx', {}).get('nonce', 0)

    @classmethod
    def get_last_tx_ts(cls, account: Optional[LocalAccount] = None, idx: int = 0, proxy: Optional[Dict] = None) -> int:
        tx = cls.get_last_tx(account, idx, proxy)
        return cls.get_ts_from_tx(tx)

    @staticmethod
    def get_nonce_from_tx(tx: dict) -> int:
        return tx.get('tx', {}).get('nonce', 0)

    @staticmethod
    def get_ts_from_tx(tx: dict)-> int:
        dt = tx.get('created_at', '')
        if not dt:
            return 0
        return int(datetime.datetime.strptime(dt[:19], '%Y-%m-%dT%H:%M:%S').timestamp())

    @staticmethod
    def get_type_from_tx(tx: dict)-> str:
        tp = tx.get('tx', {}).get('type', '')
        token = tx.get('tx', {}).get('token', 0)

        if tp == TransactionType.mint_nft.value:
            return TransactionType.mint_nft.value

        if token:
            return TransactionType.transfer_nft.value

        return TransactionType.transfer.value

    @classmethod
    def get_last_tx(cls, account: Optional[LocalAccount] = None, idx: int = 0, proxy: Optional[Dict] = None) -> dict:
        if not account:
            account = from_mnemonic(idx=idx)
        if not proxy:
            http_proxy = os.environ.get('http_proxy')
            if http_proxy:
                proxy = {
                    'http': http_proxy
                }
        res = requests.get(f'https://api.zksync.io/api/v0.1/account/{account.address}/history/0/1', proxies=proxy).json()
        if not res:
            return {}
        return res[0]


ZKSyncLiteUtils.setup_env()
