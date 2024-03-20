from web3 import Web3
from web3.types import TxReceipt
from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.consts import GAS_LIMIT_IN_ETHER
from eth_account.signers.local import LocalAccount


class Erc20Utils:

    @classmethod
    def approve_token(cls, w3: Web3, account: LocalAccount, token_address: str, to: str, count: int = 200 * 10 ** 6,
                      limit_on_gas: bool = True, multiply_gas: float = 1) -> bool:
        erc_20_abi = get_abi('erc20.json')
        token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        tx_hash = token.functions.approve(
            Web3.to_checksum_address(to), count
        ).build_transaction({
            'from': Web3.to_checksum_address(account.address),
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': int(w3.eth.gas_price * multiply_gas),
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_price = w3.eth.gas_price
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if limit_on_gas and gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, w3: Web3, account: LocalAccount, token_address: str, to: str,
                                min_approve: int = 5) -> (bool, int):
        erc_20_abi = get_abi('erc20.json')
        token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        allowance = token.functions.allowance(Web3.to_checksum_address(account.address),
                                              Web3.to_checksum_address(to)).call()
        global_logger.info(f'approved amount: {allowance}')
        return allowance > min_approve * 10 ** 6, allowance

    @classmethod
    def checking_token_totally_approved(cls, w3: Web3, account: LocalAccount, token_address: str, to: str) -> bool:
        erc_20_abi = get_abi('erc20.json')
        token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        balance = token.functions.balanceOf(account.address).call()  # returns int with balance, without decimals

        allowance = token.functions.allowance(Web3.to_checksum_address(account.address),
                                              Web3.to_checksum_address(to)).call()
        global_logger.info(f'approved amount: {allowance}')
        return allowance >= balance

    @classmethod
    def transfer_token(cls, w3: Web3, account: LocalAccount, token_address: str, to: str, value: int) -> bool:
        erc_20_abi = get_abi('erc20.json')
        token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        tx_hash = token.functions.transfer(
            Web3.to_checksum_address(to),
            value
        ).build_transaction({
            'from': Web3.to_checksum_address(account.address),
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price,
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_price = w3.eth.gas_price
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True
