import random
import time
from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.erc20_utils import Erc20Utils
from layer2.consts import TokenAddress
from layer2.consts import GAS_LIMIT_IN_ETHER


class SpaceFi:
    router_address = '0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d'

    @classmethod
    def eth_to_usdc(cls, account: LocalAccount, w3: Web3, value: int = int(0.01 * 10 ** 18)) -> bool:
        # default 0.01 * 10 ** 18 => 0.01 eth
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('spacefi/spacefi.json')
        contract = w3.eth.contract(address=Web3.to_checksum_address(cls.router_address), abi=abi)

        path = (
            Web3.to_checksum_address(TokenAddress.weth.value),
            Web3.to_checksum_address(TokenAddress.usdc.value)
        )
        gas_price = w3.eth.gas_price
        tx = contract.functions.swapExactETHForTokens(
            0,
            path,
            account.address,
            w3.to_wei(int(time.time()) + 1800, 'wei')
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'value': value,
            'gas': 1000000,
        })

        # 0x7ff36ab5
        # 0000000000000000000000000000000000000000000000000000000001042c15
        # 0000000000000000000000000000000000000000000000000000000000000080
        # 000000000000000000000000a422021ec3416ab9665ad65b1c50760bd2b1eccd
        # 0000000000000000000000000000000000000000000000000000000065e2adc2
        # 0000000000000000000000000000000000000000000000000000000000000002
        # 0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        # 0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4

        gas_estimate = w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'SpaceFI eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(
            f'SpaceFI eth=>usdc: transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def usdc_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 6) -> bool:
        # default 0.01 * 10 ** 18 => 0.01 eth
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('spacefi/spacefi.json')
        contract = w3.eth.contract(address=Web3.to_checksum_address(cls.router_address), abi=abi)
        path = (
            Web3.to_checksum_address(TokenAddress.usdc.value),
            Web3.to_checksum_address(TokenAddress.weth.value)
        )
        gas_price = w3.eth.gas_price
        tx = contract.functions.swapExactTokensForETH(
            value,
            0,
            path,
            account.address,
            w3.to_wei(int(time.time()) + 1800, 'wei')
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'SpaceFI usdc=>eth: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(
            f'SpaceFI usdc=>eth: transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, account: LocalAccount, w3: Web3, token_address: str) -> (bool, int):
        return Erc20Utils.checking_token_approved(w3, account, token_address, cls.router_address)

    @classmethod
    def approve_token(cls, account: LocalAccount, w3: Web3, token_address: str, count: int = 0) -> bool:
        if not count:
            count = random.randint(500, 2000) * 10 ** 6
        return Erc20Utils.approve_token(w3, account, token_address, cls.router_address, count)
