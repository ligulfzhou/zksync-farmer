import random
import time
from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.config.config import conf
from layer2.assets.assets import get_abi
from layer2.erc20_utils import Erc20Utils
from layer2.consts import GAS_LIMIT_IN_ETHER, TokenAddress


class Mute:

    @classmethod
    def eth_to_usdc(cls, account: LocalAccount, w3: Web3, value: int = 10 ** 16) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('mute/Router.json')
        router_contract_address = w3.to_checksum_address(conf.mute['Router'])
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)
        path = (
            Web3.to_checksum_address(TokenAddress.weth.value),
            Web3.to_checksum_address(TokenAddress.usdc.value)
        )

        gas_price = w3.eth.gas_price
        # Function: sWapExactETHForTokenssupportingFeelnTransferTokens(uint256 amountouthin, adress[] path, address to, uint25 deadline, bool[] stable)
        tx_hash = router_contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
            0,
            path,
            account.address,
            w3.to_wei(int(time.time()) + 1800, 'wei'),
            [False, False]
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'value': value,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Mute eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def usdc_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 6) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('mute/Router.json')
        router_contract_address = w3.to_checksum_address(conf.mute['Router'])
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)
        path = (
            Web3.to_checksum_address(TokenAddress.usdc.value),
            Web3.to_checksum_address(TokenAddress.weth.value)
        )

        gas_price = w3.eth.gas_price
        # Function: sWapExactETHForTokenssupportingFeelnTransferTokens(uint256 amountouthin, adress[] path, address to, uint25 deadline, bool[] stable)
        tx_hash = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
            value,
            0,
            path,
            account.address,
            w3.to_wei(int(time.time()) + 1800, 'wei'),
            [False, False]
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            # 'value': value,  # very important.
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Mute eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, account: LocalAccount, w3: Web3, token_address: str) -> (bool, int):
        return Erc20Utils.checking_token_approved(w3, account, token_address, conf.mute['Router'])

    @classmethod
    def approve_token(cls, account: LocalAccount, w3: Web3, token_address: str, count: int = 0) -> bool:
        if not count:
            count = random.randint(500, 2000) * 10 ** 6
        return Erc20Utils.approve_token(w3, account, token_address, conf.mute['Router'], count)
